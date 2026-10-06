"""Post-generation pipeline: master, verify, spectrogram, MP3, Workers sizing."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from lib.loudness import remaster_wav_file
from ship_wav import maybe_downsample_for_workers
from verify import render_spectrogram, verify_wav

SAMPLE_RATE = 48000


def export_mp3(wav_path: Path, mp3_path: Path) -> bool:
    if not shutil.which("ffmpeg"):
        return False
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(wav_path), "-q:a", "4", str(mp3_path)],
            check=True,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def run_generate_py(code_path: Path) -> None:
    if not code_path.is_file():
        raise FileNotFoundError(f"Missing generate.py: {code_path}")
    subprocess.run(
        [sys.executable, str(code_path.name)],
        cwd=str(code_path.parent),
        check=True,
    )


def apply_master_and_ship(
    entry: dict,
    wav_path: Path,
) -> str:
    master = entry.get("master") or {}
    target_lufs = float(master.get("targetLufs", -14))
    true_peak_db = float(master.get("truePeakDbTp", -1))
    remaster_wav_file(wav_path, target_lufs=target_lufs, true_peak_db=true_peak_db)
    note = ""
    if maybe_downsample_for_workers(wav_path):
        import wave

        with wave.open(str(wav_path), "rb") as wf:
            entry["timing"]["sampleRate"] = wf.getframerate()
            entry["timing"]["samples"] = wf.getnframes()
        note = " WAV shipped as 32 kHz mono for Workers 5 MiB asset limit."
    return note


def verify_entry_audio(
    entry: dict,
    wav_path: Path,
    expected_samples: int | None,
) -> dict:
    metrics = verify_wav(
        wav_path,
        expected_samples=expected_samples,
        expected_sr=int(entry["timing"].get("sampleRate", SAMPLE_RATE)),
    )
    target_lufs = float(entry.get("master", {}).get("targetLufs", -14))
    lufs_ok = metrics.get("lufs") is not None and abs(metrics["lufs"] - target_lufs) <= 1.0
    tp_ceiling = float(entry.get("master", {}).get("truePeakDbTp", -1))
    peak_ok = metrics.get("truePeak") is not None and metrics["truePeak"] <= tp_ceiling + 0.2
    metrics["passedChecks"] = bool(metrics.get("passedChecks") and lufs_ok and peak_ok)
    return metrics


def finish_entry_assets(
    entry: dict,
    wav_path: Path,
    spec_path: Path,
    mp3_path: Path,
    expected_samples: int | None,
) -> tuple[dict, str]:
    shipped_note = apply_master_and_ship(entry, wav_path)
    metrics = verify_entry_audio(entry, wav_path, expected_samples)
    try:
        render_spectrogram(wav_path, spec_path)
    except ModuleNotFoundError as exc:
        if "matplotlib" not in str(exc):
            raise
        print("warn: matplotlib missing — skip spectrogram", file=sys.stderr)
    export_mp3(wav_path, mp3_path)
    return metrics, shipped_note
