"""Mock Opus output: short synthesised stereo WAV from seed + category."""

from __future__ import annotations

import math
import struct
import wave
from pathlib import Path

import numpy as np

from lib.audio_lib import SAMPLE_RATE, master_chain, stereo, sine, DrumMachine, SynthPad

ROOT = Path(__file__).resolve().parents[1]


def write_wav(path: Path, audio_stereo: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    audio = np.clip(audio_stereo, -1, 1)
    pcm = (audio * 32767).astype(np.int16)
    with wave.open(str(path), "w") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm.tobytes())


def synthesise(category: str, duration_sec: float, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    n = int(SAMPLE_RATE * duration_sec)
    t = np.linspace(0, duration_sec, n, endpoint=False)
    dm = DrumMachine()
    pad = SynthPad()

    if category == "chaos-calm":
        chaos = dm.kick(0.15)
        chaos = np.tile(chaos, int(n * 0.4 / len(chaos)))[: int(n * 0.45)]
        chaos = np.pad(chaos, (0, max(0, n - len(chaos))))
        chaos += 0.3 * rng.standard_normal(n).astype(np.float32) * np.exp(-t * 2)
        calm = pad.render(293.66, duration_sec * 0.55, seed=seed)  # D4
        calm = np.pad(calm, (0, max(0, n - len(calm))))[:n]
        cue = int(0.35 * n)
        xfade = np.linspace(1, 0, min(int(0.08 * SAMPLE_RATE), n - cue))
        mono = chaos.copy()
        end = min(cue + len(xfade), n)
        mono[cue:end] = chaos[cue:end] * xfade[: end - cue] + calm[cue:end] * (1 - xfade[: end - cue])
        mono[end:] = calm[end:]
    elif category == "ad-beds":
        bpm = 120
        beat = int(SAMPLE_RATE * 60 / bpm)
        mono = np.zeros(n, dtype=np.float32)
        for i in range(0, n, beat):
            kick = dm.kick(0.12)
            mono[i : i + len(kick)] += kick * 0.6
        mono += 0.25 * pad.render(440, duration_sec, seed=seed)[:n]
        mono += 0.1 * sine(880, duration_sec)[:n]
    elif category == "drops":
        mono = np.zeros(n, dtype=np.float32)
        hit = int(0.15 * n)
        tail = n - hit
        kick = dm.kick(0.4)
        if len(kick) > tail:
            kick = kick[:tail]
        else:
            kick = np.pad(kick, (0, tail - len(kick)))
        mono[hit:] += kick * np.exp(-np.linspace(0, 3, tail))
        mono += 0.2 * rng.standard_normal(n).astype(np.float32) * (t > duration_sec * 0.12)
    elif category == "risers":
        freqs = np.linspace(200, 2000, n)
        mono = np.sin(2 * np.pi * np.cumsum(freqs / SAMPLE_RATE)) * np.linspace(0, 1, n)
        mono = mono.astype(np.float32)
    elif category == "ui-sounds":
        ping_len = int(0.08 * SAMPLE_RATE)
        ping = sine(1200, ping_len / SAMPLE_RATE) * np.exp(-np.linspace(0, 12, ping_len))
        mono = np.zeros(n, dtype=np.float32)
        mono[:ping_len] = ping
        mono[int(0.02 * SAMPLE_RATE) : int(0.02 * SAMPLE_RATE) + ping_len] += ping * 0.5
    elif category == "logo-stings":
        mono = pad.render(523.25, min(duration_sec, 2.0), seed=seed)
        mono = np.pad(mono, (0, max(0, n - len(mono))))[:n]
        mono += 0.3 * sine(1046.5, duration_sec)[:n] * np.exp(-t * 4)
    elif category == "ambient":
        mono = 0.4 * pad.render(220, duration_sec, seed=seed)[:n]
        mono += 0.15 * pad.render(277.18, duration_sec, seed=seed + 1)[:n]
        mono += 0.05 * rng.standard_normal(n).astype(np.float32)
    else:
        mono = 0.3 * sine(440, duration_sec)

    fade = int(0.05 * SAMPLE_RATE)
    mono[:fade] *= np.linspace(0, 1, fade)
    mono[-fade:] *= np.linspace(1, 0, fade)
    mono = master_chain(mono)
    return stereo(mono)


def write_code_stub(path: Path, entry_id: str, prompt: str, seed: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f'''"""Generated sound code for {entry_id} (mock stub). Seed={seed}."""
import numpy as np
from runner.lib.audio_lib import SAMPLE_RATE, master_chain, stereo

# Prompt (truncated in stub):
# {prompt[:200].replace(chr(10), " ")}...

def generate(seed: int = {seed}) -> np.ndarray:
    rng = np.random.default_rng(seed)
    duration_sec = ...  # see entry timing
    # Full synthesis would be implemented here per prompt.
    t = np.linspace(0, duration_sec, int(SAMPLE_RATE * duration_sec), endpoint=False)
    mono = 0.2 * np.sin(2 * np.pi * 440 * t)
    return stereo(master_chain(mono))
''',
        encoding="utf-8",
    )


def integrated_lufs_estimate(mono: np.ndarray) -> float:
    """Rough LUFS proxy when ffmpeg ebur128 is unavailable."""
    rms = float(np.sqrt(np.mean(mono ** 2)))
    if rms < 1e-10:
        return -70.0
    return round(20 * math.log10(rms) - 0.691, 2)


def true_peak_db(mono: np.ndarray) -> float:
    peak = float(np.max(np.abs(mono)))
    if peak < 1e-10:
        return -70.0
    return round(20 * math.log10(peak), 2)
