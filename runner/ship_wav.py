"""Downsample oversized WAVs for Workers 5 MiB static asset limit."""

from __future__ import annotations

import shutil
import subprocess
import wave
from pathlib import Path

MAX_BYTES = 4_800_000
SHIP_RATES = (32000, 24000, 22050, 16000)


def maybe_downsample_for_workers(wav_path: Path) -> bool:
    if wav_path.stat().st_size <= MAX_BYTES:
        return False
    if not shutil.which("ffmpeg"):
        return False
    shipped = False
    for sr in SHIP_RATES:
        tmp = wav_path.with_suffix(f".ship-{sr}.wav")
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-i",
                str(wav_path),
                "-ac",
                "2",
                "-ar",
                str(sr),
                str(tmp),
            ],
            check=True,
        )
        if tmp.stat().st_size <= MAX_BYTES:
            tmp.replace(wav_path)
            shipped = True
            break
        tmp.unlink(missing_ok=True)
    if not shipped:
        raise RuntimeError(f"Could not ship {wav_path} under {MAX_BYTES} bytes (stereo)")
    return True


def shipped_sample_rate(wav_path: Path) -> int:
    with wave.open(str(wav_path), "rb") as wf:
        return wf.getframerate()
