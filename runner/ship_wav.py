"""Downsample oversized WAVs for Workers 5 MiB static asset limit."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

MAX_BYTES = 4_800_000
SHIP_SR = 32000


def maybe_downsample_for_workers(wav_path: Path) -> bool:
    if wav_path.stat().st_size <= MAX_BYTES:
        return False
    if not shutil.which("ffmpeg"):
        return False
    tmp = wav_path.with_suffix(".ship.wav")
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
            str(SHIP_SR),
            str(tmp),
        ],
        check=True,
    )
    tmp.replace(wav_path)
    return True
