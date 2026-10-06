"""Synthesis code for ambient-bed-lofi. Run: python generate.py (writes out.wav)."""
from __future__ import annotations

from pathlib import Path

import numpy as np

import math
import wave
from pathlib import Path

import numpy as np

SAMPLE_RATE = 48000


def t_grid(duration_sec: float) -> np.ndarray:
    n = int(SAMPLE_RATE * duration_sec)
    return np.linspace(0, duration_sec, n, endpoint=False, dtype=np.float64)


def sine(freq: float, duration_sec: float, phase: float = 0.0) -> np.ndarray:
    tt = t_grid(duration_sec)
    return np.sin(2 * np.pi * freq * tt + phase).astype(np.float32)


def envelope_adsr(
    length: int,
    attack: float = 0.01,
    decay: float = 0.05,
    sustain: float = 0.7,
    release: float = 0.12,
) -> np.ndarray:
    a = max(1, int(attack * SAMPLE_RATE))
    d = max(1, int(decay * SAMPLE_RATE))
    r = max(1, int(release * SAMPLE_RATE))
    s = max(0, length - a - d - r)
    env = np.concatenate(
        [
            np.linspace(0, 1, a),
            np.linspace(1, sustain, d),
            np.full(s, sustain),
            np.linspace(sustain, 0, r),
        ]
    )
    if len(env) < length:
        env = np.pad(env, (0, length - len(env)))
    return env[:length].astype(np.float32)


def soft_clip(x: np.ndarray, drive: float = 1.15) -> np.ndarray:
    return np.tanh(x * drive).astype(np.float32)


def limiter(x: np.ndarray, ceiling: float = 0.89) -> np.ndarray:
    peak = float(np.max(np.abs(x)))
    if peak > ceiling and peak > 0:
        x = x * (ceiling / peak)
    return x.astype(np.float32)


def stereo(mono: np.ndarray, width: float = 0.12) -> np.ndarray:
    n = len(mono)
    pan = np.linspace(-width, width, n).astype(np.float32)
    left = mono * (1 - pan)
    right = mono * (1 + pan)
    return np.stack([left, right], axis=-1)


def fade_edges(mono: np.ndarray, sec: float = 0.03) -> np.ndarray:
    f = max(1, int(sec * SAMPLE_RATE))
    mono = mono.copy()
    mono[:f] *= np.linspace(0, 1, f)
    mono[-f:] *= np.linspace(1, 0, f)
    return mono


def integrated_lufs_estimate(mono: np.ndarray) -> float:
    rms = float(np.sqrt(np.mean(mono**2)))
    if rms < 1e-10:
        return -70.0
    return 20 * math.log10(rms) - 0.691


def _as_stereo(audio: np.ndarray) -> np.ndarray:
    if audio.ndim == 1:
        return np.stack([audio, audio], axis=-1)
    return audio


def integrated_lufs_stereo(stereo: np.ndarray) -> float:
    import pyloudnorm as pyln

    st = _as_stereo(stereo).astype(np.float64)
    meter = pyln.Meter(SAMPLE_RATE)
    try:
        return float(meter.integrated_loudness(st))
    except Exception:
        mono = st.mean(axis=1)
        return integrated_lufs_estimate(mono.astype(np.float32))


def normalize_lufs_stereo(stereo: np.ndarray, target: float = -14.0) -> np.ndarray:
    import pyloudnorm as pyln

    st = _as_stereo(stereo).astype(np.float64)
    st -= np.mean(st, axis=0, keepdims=True)
    meter = pyln.Meter(SAMPLE_RATE)
    try:
        loud = meter.integrated_loudness(st)
        if loud > -70:
            st = pyln.normalize.loudness(st, loud, target)
    except Exception:
        mono = st.mean(axis=1).astype(np.float32)
        gain = 10 ** ((target - integrated_lufs_estimate(mono)) / 20)
        st = st * gain
    return st.astype(np.float32)


def master_stereo(
    stereo: np.ndarray,
    target_lufs: float = -14.0,
    true_peak_db: float = -1.0,
) -> np.ndarray:
    st = normalize_lufs_stereo(stereo, target_lufs)
    ceiling = 10 ** (true_peak_db / 20.0)
    for _ in range(8):
        st = soft_clip(st, 1.05)
        peak = float(np.max(np.abs(st)))
        if peak > ceiling and peak > 0:
            st = st * (ceiling / peak)
        loud = integrated_lufs_stereo(st.astype(np.float64))
        if abs(loud - target_lufs) > 0.45:
            st = normalize_lufs_stereo(st, target_lufs)
    peak = float(np.max(np.abs(st)))
    if peak > ceiling and peak > 0:
        st = st * (ceiling / peak)
    return st.astype(np.float32)


def master_chain(mono: np.ndarray, target_lufs: float = -14.0, true_peak_db: float = -1.0) -> np.ndarray:
    """Mono convenience wrapper — loudness measured on duplicated stereo (matches ffmpeg ebur128)."""
    return master_stereo(stereo(mono, width=0.0), target_lufs, true_peak_db).mean(axis=1).astype(np.float32)


def kick(duration: float = 0.18, seed: int = 0) -> np.ndarray:
    tt = t_grid(duration)
    pitch = 58 * np.exp(-tt * 36)
    body = np.sin(2 * np.pi * pitch * tt) * np.exp(-tt * 14)
    click = np.random.default_rng(seed).standard_normal(len(tt)).astype(np.float32)
    click *= np.exp(-tt * 80) * 0.15
    return (body + click).astype(np.float32)


def hihat(duration: float = 0.06, seed: int = 0) -> np.ndarray:
    n = int(SAMPLE_RATE * duration)
    rng = np.random.default_rng(seed)
    noise = rng.standard_normal(n).astype(np.float32)
    env = np.exp(-np.linspace(0, 18, n))
    return noise * env * 0.35


def clap(duration: float = 0.12, seed: int = 0) -> np.ndarray:
    n = int(SAMPLE_RATE * duration)
    rng = np.random.default_rng(seed)
    bursts = np.zeros(n, dtype=np.float32)
    for off in (0, 0.008, 0.016):
        i = int(off * SAMPLE_RATE)
        blen = min(n - i, int(0.04 * SAMPLE_RATE))
        if blen <= 0:
            continue
        b = rng.standard_normal(blen).astype(np.float32)
        b *= np.exp(-np.linspace(0, 10, blen))
        bursts[i : i + blen] += b
    return bursts * 0.5


def pluck(freq: float, duration: float, seed: int = 0) -> np.ndarray:
    n = int(SAMPLE_RATE * duration)
    tt = np.linspace(0, duration, n, endpoint=False)
    rng = np.random.default_rng(seed)
    partials = [1.0, 0.5, 0.25, 0.12]
    sig = np.zeros(n, dtype=np.float32)
    for i, amp in enumerate(partials):
        sig += amp * np.sin(2 * np.pi * freq * (i + 1) * tt + rng.uniform(0, 0.2))
    env = envelope_adsr(n, attack=0.002, decay=0.08, sustain=0.15, release=0.2)
    return sig * env


def bass(freq: float, duration: float) -> np.ndarray:
    n = int(SAMPLE_RATE * duration)
    tt = np.linspace(0, duration, n, endpoint=False)
    sig = np.sin(2 * np.pi * freq * tt) + 0.35 * np.sin(2 * np.pi * freq * 2 * tt)
    env = envelope_adsr(n, attack=0.01, decay=0.1, sustain=0.6, release=0.15)
    return (sig * env * 0.55).astype(np.float32)


def pad_layers(root: float, duration: float, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    freqs = [root, root * 1.25, root * 1.5, root * 2.0]
    n = int(SAMPLE_RATE * duration)
    mix = np.zeros(n, dtype=np.float32)
    for f in freqs:
        layer = sine(f * (1 + rng.uniform(-0.008, 0.008)), duration)
        mix += layer
    env = envelope_adsr(n, attack=0.4, decay=0.2, sustain=0.75, release=0.5)
    return (mix / len(freqs) * env).astype(np.float32)


def piano_tone(freq: float, duration: float, seed: int = 0) -> np.ndarray:
    return pluck(freq, duration, seed=seed) * 0.85


def noise_burst(duration: float, seed: int = 0) -> np.ndarray:
    n = int(SAMPLE_RATE * duration)
    rng = np.random.default_rng(seed)
    return (rng.standard_normal(n) * np.exp(-np.linspace(0, 6, n))).astype(np.float32)


def bandpass_noise(duration: float, f0: float, f1: float, seed: int = 0) -> np.ndarray:
    n = int(SAMPLE_RATE * duration)
    rng = np.random.default_rng(seed)
    noise = rng.standard_normal(n)
    # simple sweepable resonant filter via cumulative sine modulation
    tt = np.linspace(0, duration, n, endpoint=False)
    freq = np.linspace(f0, f1, n)
    mod = np.sin(2 * np.pi * freq * tt)
    return (noise * mod * np.linspace(0.2, 1, n)).astype(np.float32)


def whoosh_riser(duration: float, seed: int = 0) -> np.ndarray:
    n = int(SAMPLE_RATE * duration)
    tt = np.linspace(0, duration, n, endpoint=False)
    freqs = np.linspace(200, 4000, n)
    phase = np.cumsum(freqs / SAMPLE_RATE) * 2 * np.pi
    tone = np.sin(phase) * np.linspace(0.05, 0.9, n)
    noise = bandpass_noise(duration, 300, 8000, seed=seed) * np.linspace(0.1, 0.7, n)
    return (tone + noise).astype(np.float32)


def metallic_hit(seed: int = 0) -> np.ndarray:
    dur = 0.35
    n = int(SAMPLE_RATE * dur)
    tt = np.linspace(0, dur, n, endpoint=False)
    rng = np.random.default_rng(seed)
    freqs = [880, 1320, 1760, 2210]
    sig = np.zeros(n, dtype=np.float32)
    for f in freqs:
        sig += np.sin(2 * np.pi * f * tt) * np.exp(-tt * (8 + rng.uniform(0, 4)))
    _mix_at(sig, 0, noise_burst(0.08, seed=seed + 1), 0.4)
    return sig


def ui_chime_pair(f1: float, f2: float, duration: float, seed: int = 0) -> np.ndarray:
    n = int(SAMPLE_RATE * duration)
    mono = np.zeros(n, dtype=np.float32)
    a = pluck(f1, duration * 0.55, seed=seed)
    b = pluck(f2, duration * 0.65, seed=seed + 1)
    mono[: len(a)] += a
    offset = int(0.08 * SAMPLE_RATE)
    mono[offset : offset + len(b)] += b * 0.85
    return mono[:n]


def _mix_at(mono: np.ndarray, pos: int, snippet: np.ndarray, gain: float = 1.0) -> None:
    end = min(len(mono), pos + len(snippet))
    if pos >= end:
        return
    mono[pos:end] += snippet[: end - pos] * gain


def chaos_clocks(duration: float, seed: int = 0) -> np.ndarray:
    n = int(SAMPLE_RATE * duration)
    mono = np.zeros(n, dtype=np.float32)
    rng = np.random.default_rng(seed)
    for _ in range(24):
        pos = rng.integers(0, max(1, n - int(0.2 * SAMPLE_RATE)))
        tick = pluck(1800 + rng.uniform(-400, 400), 0.08, seed=int(rng.integers(0, 1_000_000)))
        _mix_at(mono, pos, tick, 0.35)
    _mix_at(mono, 0, noise_burst(min(duration, 0.4), seed=seed), 0.25)
    for i in range(0, n, int(SAMPLE_RATE * 0.5)):
        _mix_at(mono, i, kick(0.1, seed=seed + i), 0.5)
    return mono


def chaos_traffic(duration: float, seed: int = 0) -> np.ndarray:
    n = int(SAMPLE_RATE * duration)
    mono = np.zeros(n, dtype=np.float32)
    rng = np.random.default_rng(seed)
    for _ in range(18):
        pos = rng.integers(0, max(1, n - 4000))
        honk = sine(220 + rng.uniform(-40, 40), 0.25) * envelope_adsr(int(0.25 * SAMPLE_RATE), 0.01, 0.05, 0.4, 0.1)
        end = min(n, pos + len(honk))
        _mix_at(mono, pos, honk, 0.4)
    _mix_at(mono, 0, bandpass_noise(duration, 400, 2500, seed=seed), 0.2)
    return mono


def crossfade_at(chaos: np.ndarray, calm: np.ndarray, cue: int, xfade_sec: float = 0.35) -> np.ndarray:
    n = len(chaos)
    calm = calm[:n]
    if len(calm) < n:
        calm = np.pad(calm, (0, n - len(calm)))
    xf = int(xfade_sec * SAMPLE_RATE)
    out = chaos.copy()
    end = min(n, cue + xf)
    ramp = np.linspace(1, 0, max(1, end - cue))
    out[cue:end] = chaos[cue:end] * ramp[: end - cue] + calm[cue:end] * (1 - ramp[: end - cue])
    out[end:] = calm[end:]
    return fade_edges(out, 0.04)


def write_wav(path: Path, stereo_audio: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    audio = np.clip(stereo_audio, -1, 1)
    pcm = (audio * 32767).astype(np.int16)
    with wave.open(str(path), "w") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm.tobytes())


E3, B3, D4, A3 = 164.81, 246.94, 293.66, 220.0

def _n(duration: float) -> int:
    return int(SAMPLE_RATE * duration)

def _add(mono: np.ndarray, pos: int, snippet: np.ndarray, gain: float = 1.0) -> None:
    end = min(len(mono), pos + len(snippet))
    if pos >= end:
        return
    mono[pos:end] += snippet[: end - pos] * gain

def synth_ambient_bed_lofi(duration: float, seed: int) -> np.ndarray:
    mono = pad_layers(220, duration, seed=seed) * 0.55
    mono += pad_layers(277.18, duration, seed=seed + 1) * 0.35
    _add(mono, int(2.5 * SAMPLE_RATE), pluck(440, 0.8, seed=seed), 0.08)
    return stereo(master_chain(mono, target_lufs=-16.0))


def generate(seed: int = 42) -> np.ndarray:
    return synth_ambient_bed_lofi(12, seed)


if __name__ == "__main__":
    out = Path(__file__).resolve().parent / "out.wav"
    write_wav(out, generate())
    print(f"Wrote {out}")
