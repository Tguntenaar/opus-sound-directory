"""Verification: length, loudness, peak, spectrogram."""

from __future__ import annotations

import shutil
import subprocess
import wave
from pathlib import Path

import numpy as np

from mock_generate import integrated_lufs_estimate, true_peak_db

SAMPLE_RATE = 48000


def read_wav_mono(path: Path) -> tuple[np.ndarray, int, int]:
    with wave.open(str(path), "rb") as wf:
        ch = wf.getnchannels()
        sr = wf.getframerate()
        frames = wf.readframes(wf.getnframes())
    samples = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
    if ch == 2:
        samples = samples.reshape(-1, 2).mean(axis=1)
    return samples, sr, len(samples)


def ffmpeg_ebur128(path: Path) -> dict[str, float | None]:
    if not shutil.which("ffmpeg"):
        return {"lufs": None, "truePeak": None}
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-i",
        str(path),
        "-af",
        "ebur128=peak=true",
        "-f",
        "null",
        "-",
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        text = proc.stderr
        lufs = None
        peak = None
        for line in text.splitlines():
            if "I:" in line and "LUFS" in line:
                parts = line.split("I:")[1].split("LUFS")[0].strip()
                try:
                    lufs = float(parts)
                except ValueError:
                    pass
            if "Peak:" in line and "dBFS" in line:
                try:
                    peak = float(line.split("Peak:")[1].split("dBFS")[0].strip())
                except ValueError:
                    pass
        return {"lufs": lufs, "truePeak": peak}
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return {"lufs": None, "truePeak": None}


def render_spectrogram(wav_path: Path, out_png: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    mono, sr, _ = read_wav_mono(wav_path)
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(10, 3), dpi=100)
    ax.specgram(mono, NFFT=1024, Fs=sr, noverlap=512, cmap="magma")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Freq (Hz)")
    ax.set_title("Spectrogram")
    fig.tight_layout()
    fig.savefig(out_png, facecolor="#0f0f12")
    plt.close(fig)


def verify_wav(
    path: Path,
    expected_samples: int | None,
    expected_sr: int = SAMPLE_RATE,
) -> dict:
    mono, sr, n = read_wav_mono(path)
    ff = ffmpeg_ebur128(path)
    lufs = ff["lufs"] if ff["lufs"] is not None else integrated_lufs_estimate(mono)
    peak = ff["truePeak"] if ff["truePeak"] is not None else true_peak_db(mono)
    length_ok = expected_samples is None or n == expected_samples
    sr_ok = sr == expected_sr
    passed = length_ok and sr_ok and peak <= 0.0
    return {
        "lufs": lufs,
        "truePeak": peak,
        "durationSec": round(n / sr, 4),
        "samples": n,
        "passedChecks": passed,
        "lengthOk": length_ok,
        "sampleRateOk": sr_ok,
    }
