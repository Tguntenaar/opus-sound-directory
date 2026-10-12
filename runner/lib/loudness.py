"""Shared loudness mastering for runner pipeline and embedded generate.py runtime."""

from __future__ import annotations

import sys
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "runner" / "templates"))
from synth_runtime import (  # noqa: E402
    SAMPLE_RATE,
    fade_edges,
    integrated_lufs_stereo,
    master_stereo,
    write_wav,
)


def read_wav_stereo(path: Path) -> tuple[np.ndarray, int]:
    with wave.open(str(path), "rb") as wf:
        ch = wf.getnchannels()
        sr = wf.getframerate()
        frames = wf.readframes(wf.getnframes())
    samples = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
    if ch == 1:
        stereo = np.stack([samples, samples], axis=-1)
    else:
        stereo = samples.reshape(-1, ch)
        if ch > 2:
            stereo = stereo[:, :2]
    return stereo.astype(np.float32), sr


def write_wav_stereo(path: Path, stereo: np.ndarray, sample_rate: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    audio = np.clip(stereo, -1, 1)
    pcm = (audio * 32767).astype(np.int16)
    with wave.open(str(path), "w") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm.tobytes())


def remaster_wav_file(
    path: Path,
    target_lufs: float = -14.0,
    true_peak_db: float = -1.0,
) -> None:
    stereo, sr = read_wav_stereo(path)
    if sr != SAMPLE_RATE:
        raise ValueError(f"Expected {SAMPLE_RATE} Hz, got {sr} in {path}")
    stereo = stereo - np.mean(stereo, axis=0, keepdims=True)
    mono = stereo.mean(axis=1)
    mono = fade_edges(mono, 0.008)
    stereo = np.stack([mono, mono], axis=-1)
    stereo = master_stereo(stereo, target_lufs=target_lufs, true_peak_db=true_peak_db)
    write_wav(path, stereo)


def remaster_wav_file_any_rate(
    path: Path,
    target_lufs: float = -14.0,
    true_peak_db: float = -1.0,
) -> None:
    """Peak/loudness repair for shipped downsampled WAVs (e.g. 32 kHz Workers assets)."""
    import pyloudnorm as pyln

    stereo, sr = read_wav_stereo(path)
    stereo = stereo - np.mean(stereo, axis=0, keepdims=True)
    f = max(1, int(0.008 * sr))
    mono = stereo.mean(axis=1).copy()
    mono[:f] *= np.linspace(0, 1, f)
    mono[-f:] *= np.linspace(1, 0, f)
    stereo = np.stack([mono, mono], axis=-1).astype(np.float64)
    meter = pyln.Meter(sr)
    try:
        loud = meter.integrated_loudness(stereo)
        if loud > -70:
            stereo = pyln.normalize.loudness(stereo, loud, target_lufs)
    except Exception:
        pass
    stereo = stereo.astype(np.float32)
    ceiling = 10 ** (true_peak_db / 20.0)
    for _ in range(6):
        peak = float(np.max(np.abs(stereo)))
        if peak > ceiling and peak > 0:
            stereo *= ceiling / peak
        loud = float(meter.integrated_loudness(stereo.astype(np.float64)))
        if abs(loud - target_lufs) > 0.35:
            stereo = pyln.normalize.loudness(stereo.astype(np.float64), loud, target_lufs).astype(
                np.float32
            )
    peak = float(np.max(np.abs(stereo)))
    if peak > ceiling and peak > 0:
        stereo *= ceiling / peak
    write_wav_stereo(path, stereo, sr)


def loudness_within_target(
    measured_lufs: float | None,
    target_lufs: float,
    tolerance_lu: float = 1.0,
) -> bool:
    if measured_lufs is None:
        return False
    return abs(measured_lufs - target_lufs) <= tolerance_lu
