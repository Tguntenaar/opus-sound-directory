"""Post-generation pipeline: master, verify, spectrogram, MP3, Workers sizing."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from lib.loudness import remaster_wav_file
from ship_wav import maybe_downsample_for_workers
from verify import ffmpeg_ebur128, render_spectrogram, verify_wav

# libmp3lame can raise decoded true peak above the PCM source; pre-limit and verify.
_MP3_PRE_LIMIT_DBTP = (-1.35, -1.5, -1.7, -2.0, -2.5, -3.0)
_MP3_TRUE_PEAK_CEILING_DBTP = -1.0

SAMPLE_RATE = 48000
LUFS_TOLERANCE_LU = 0.5
ROOT = Path(__file__).resolve().parents[1]
MASTER_ROOT = ROOT / "masters"


def save_master_wav(entry_id: str, wav_path: Path) -> None:
    dest_dir = MASTER_ROOT / entry_id
    dest_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(wav_path, dest_dir / "out.wav")


def limit_wav_true_peak_ffmpeg(wav_path: Path, ceiling_db: float) -> bool:
    """In-place true-peak limit via ffmpeg (any sample rate)."""
    if not shutil.which("ffmpeg"):
        return False
    tmp = wav_path.with_suffix(".peak-limit.wav")
    af = f"alimiter=limit={ceiling_db}dB:attack=1:release=50:level=false"
    try:
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-i",
                str(wav_path),
                "-af",
                af,
                str(tmp),
            ],
            check=True,
        )
        tmp.replace(wav_path)
        return True
    except subprocess.CalledProcessError:
        tmp.unlink(missing_ok=True)
        return False


def export_mp3(wav_path: Path, mp3_path: Path) -> bool:
    if not shutil.which("ffmpeg"):
        return False
    for pre_limit in _MP3_PRE_LIMIT_DBTP:
        af = f"alimiter=limit={pre_limit}dB:attack=1:release=50:level=false"
        try:
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-i",
                    str(wav_path),
                    "-af",
                    af,
                    "-q:a",
                    "2",
                    str(mp3_path),
                ],
                check=True,
            )
        except subprocess.CalledProcessError:
            continue
        metrics = ffmpeg_ebur128(mp3_path)
        peak = metrics.get("truePeak")
        if peak is not None and peak <= _MP3_TRUE_PEAK_CEILING_DBTP:
            return True
    return False


def run_generate_py(code_path: Path) -> None:
    if not code_path.is_file():
        raise FileNotFoundError(f"Missing generate.py: {code_path}")
    subprocess.run(
        [sys.executable, str(code_path.name)],
        cwd=str(code_path.parent),
        check=True,
    )


def remaster_entry_wav(entry: dict, wav_path: Path) -> None:
    master = entry.get("master") or {}
    target_lufs = float(master.get("targetLufs", -14))
    true_peak_db = float(master.get("truePeakDbTp", -1))
    remaster_wav_file(wav_path, target_lufs=target_lufs, true_peak_db=true_peak_db)


def ship_wav_for_workers(entry: dict, wav_path: Path) -> str:
    note = ""
    if maybe_downsample_for_workers(wav_path):
        import wave

        with wave.open(str(wav_path), "rb") as wf:
            entry["timing"]["sampleRate"] = wf.getframerate()
            entry["timing"]["samples"] = wf.getnframes()
        note = " WAV shipped as 32 kHz stereo for Workers 5 MiB asset limit."
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
    lufs_ok = metrics.get("lufs") is not None and abs(metrics["lufs"] - target_lufs) <= LUFS_TOLERANCE_LU
    tp_ceiling = float(entry.get("master", {}).get("truePeakDbTp", -1))
    peak_ok = metrics.get("truePeak") is not None and metrics["truePeak"] <= tp_ceiling + 0.05
    metrics["passedChecks"] = bool(
        metrics.get("lengthOk")
        and metrics.get("sampleRateOk")
        and lufs_ok
        and peak_ok
    )
    return metrics


def finish_entry_assets(
    entry: dict,
    wav_path: Path,
    spec_path: Path,
    mp3_path: Path,
    expected_samples: int | None,
) -> tuple[dict, str]:
    remaster_entry_wav(entry, wav_path)
    save_master_wav(entry["id"], wav_path)
    export_mp3(wav_path, mp3_path)
    shipped_note = ship_wav_for_workers(entry, wav_path)
    expected_samples = entry["timing"].get("samples", expected_samples)
    metrics = verify_entry_audio(entry, wav_path, expected_samples)
    try:
        render_spectrogram(wav_path, spec_path)
    except ModuleNotFoundError as exc:
        if "matplotlib" not in str(exc):
            raise
        print("warn: matplotlib missing — skip spectrogram", file=sys.stderr)
    return metrics, shipped_note
