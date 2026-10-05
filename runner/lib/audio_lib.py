"""
Shared audio synthesis hooks for Opus-generated sound code.

Intended API for full implementations (MVP stubs documented here).
"""

from __future__ import annotations

import numpy as np
from typing import Callable


SAMPLE_RATE = 48000


def sine(freq: float, duration_sec: float, phase: float = 0.0) -> np.ndarray:
    t = np.linspace(0, duration_sec, int(SAMPLE_RATE * duration_sec), endpoint=False)
    return np.sin(2 * np.pi * freq * t + phase).astype(np.float32)


def envelope_adsr(
    length: int,
    attack: float = 0.01,
    decay: float = 0.05,
    sustain: float = 0.7,
    release: float = 0.1,
) -> np.ndarray:
    """Return ADSR envelope array of `length` samples."""
    sr = SAMPLE_RATE
    a = int(attack * sr)
    d = int(decay * sr)
    r = int(release * sr)
    s = max(0, length - a - d - r)
    env = np.concatenate(
        [
            np.linspace(0, 1, max(a, 1)),
            np.linspace(1, sustain, max(d, 1)),
            np.full(s, sustain),
            np.linspace(sustain, 0, max(r, 1)),
        ]
    )
    if len(env) < length:
        env = np.pad(env, (0, length - len(env)), constant_values=0)
    return env[:length].astype(np.float32)


def soft_clip(x: np.ndarray, drive: float = 1.2) -> np.ndarray:
    return np.tanh(x * drive).astype(np.float32)


def limiter(x: np.ndarray, ceiling: float = 0.89) -> np.ndarray:
    """Simple brick-wall style limiter (ceiling ~ -1 dBTP for float peak 1.0)."""
    peak = np.max(np.abs(x))
    if peak > ceiling and peak > 0:
        x = x * (ceiling / peak)
    return x.astype(np.float32)


def stereo(mono: np.ndarray) -> np.ndarray:
    return np.stack([mono, mono], axis=-1)


def apply_reverb(mono: np.ndarray, mix: float = 0.15, decay: float = 0.4) -> np.ndarray:
    """Placeholder reverb: short comb of delays (replace with impulse response later)."""
    out = mono.copy()
    for delay_ms in (23, 47, 71):
        d = int(SAMPLE_RATE * delay_ms / 1000)
        if d < len(mono):
            wet = np.zeros_like(mono)
            wet[d:] = mono[:-d] * decay
            out = out + wet * mix
    return soft_clip(out)


class DrumMachine:
    """Kick / snare / hat sketch — extend with per-hit synthesis."""

    def kick(self, duration_sec: float = 0.2) -> np.ndarray:
        t = np.linspace(0, duration_sec, int(SAMPLE_RATE * duration_sec), endpoint=False)
        pitch = 60 * np.exp(-t * 40)
        return (np.sin(2 * np.pi * pitch * t) * np.exp(-t * 12)).astype(np.float32)

    def noise_burst(self, duration_sec: float = 0.05) -> np.ndarray:
        n = int(SAMPLE_RATE * duration_sec)
        return (np.random.default_rng(0).standard_normal(n) * np.exp(-np.linspace(0, 8, n))).astype(
            np.float32
        )


class SynthPad:
    """Warm pad: stacked detuned sines."""

    def render(self, freq: float, duration_sec: float, seed: int = 0) -> np.ndarray:
        rng = np.random.default_rng(seed)
        layers = [sine(freq * (1 + rng.uniform(-0.01, 0.01)), duration_sec) for _ in range(4)]
        pad = sum(layers) / len(layers)
        env = envelope_adsr(len(pad), attack=0.3, release=0.4)
        return (pad * env).astype(np.float32)


def master_chain(mono: np.ndarray, target_peak: float = 0.89) -> np.ndarray:
    return limiter(soft_clip(mono), ceiling=target_peak)


def render_with_cues(
    duration_sec: float,
    chaos_fn: Callable[[], np.ndarray],
    calm_fn: Callable[[], np.ndarray],
    cue_sec: float,
) -> np.ndarray:
    """Crossfade chaos → calm at cue time."""
    n = int(SAMPLE_RATE * duration_sec)
    cue = int(cue_sec * SAMPLE_RATE)
    chaos = chaos_fn()[:n]
    calm = calm_fn()[:n]
    if len(chaos) < n:
        chaos = np.pad(chaos, (0, n - len(chaos)))
    if len(calm) < n:
        calm = np.pad(calm, (0, n - len(calm)))
    xfade = np.linspace(1, 0, min(n - cue, int(0.5 * SAMPLE_RATE)))
    out = chaos.copy()
    end = min(cue + len(xfade), n)
    out[cue:end] = chaos[cue:end] * xfade[: end - cue] + calm[cue:end] * (1 - xfade[: end - cue])
    out[end:] = calm[end:]
    fade_len = int(0.25 * SAMPLE_RATE)
    out[-fade_len:] *= np.linspace(1, 0, fade_len)
    return master_chain(out)
