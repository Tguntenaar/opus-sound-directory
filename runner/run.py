#!/usr/bin/env python3
"""
Opus Sound Directory runner.

Mock mode (default): per-entry numpy synthesis, executable generate.py, ffmpeg metrics.
Future: wire Claude Agent SDK or `claude -p` via --agent flag (interface only in MVP).
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from code_writer import write_generate_py
from mock_generate import write_wav
from ship_wav import maybe_downsample_for_workers
from entry_meta import apply_entry_meta
from synth.entry_synth import synthesise_for_entry
from verify import render_spectrogram, verify_wav

SAMPLE_RATE = 48000


def load_entry(entry_path: Path) -> dict:
    return json.loads(entry_path.read_text(encoding="utf-8"))


def save_entry(entry_path: Path, data: dict) -> None:
    entry_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def run_entry(
    entry_path: Path,
    mock: bool = True,
    best_of: int = 1,
) -> dict:
    entry = load_entry(entry_path)
    entry_id = entry["id"]
    timing = entry.get("timing", {})
    duration = float(timing.get("durationSec", 3))
    expected_samples = timing.get("samples")
    seed = int(entry.get("seed", 42))
    asset_dir = ROOT / "public" / "assets" / entry_id
    wav_path = asset_dir / "out.wav"
    spec_path = asset_dir / "spectrogram.png"
    code_path = asset_dir / "generate.py"

    best_metrics = None
    best_seed = seed
    shipped_note = ""

    for attempt in range(best_of):
        attempt_seed = seed + attempt
        if mock:
            entry["seed"] = attempt_seed
            audio = synthesise_for_entry(entry)
            write_wav(wav_path, audio)
            write_generate_py(code_path, entry)
        else:
            raise NotImplementedError(
                "Agent mode not configured. Set ANTHROPIC_API_KEY and implement agent_generate(). "
                "See README for `claude -p` integration notes."
            )

        if maybe_downsample_for_workers(wav_path):
            import wave

            with wave.open(str(wav_path), "rb") as wf:
                sr = wf.getframerate()
                samples = wf.getnframes()
            entry["timing"]["sampleRate"] = sr
            entry["timing"]["samples"] = samples
            expected_samples = samples
            shipped_note = " WAV shipped as 32 kHz mono for Workers 5 MiB asset limit."

        metrics = verify_wav(
            wav_path,
            expected_samples=expected_samples,
            expected_sr=int(entry["timing"].get("sampleRate", SAMPLE_RATE)),
        )
        render_spectrogram(wav_path, spec_path)

        if best_metrics is None or (metrics.get("lufs") or -70) > (best_metrics.get("lufs") or -70):
            best_metrics = metrics
            best_seed = attempt_seed

    entry["seed"] = best_seed
    entry["generatedAt"] = date.today().isoformat()
    apply_entry_meta(entry, agent_mode=not mock)
    entry["metrics"] = {
        "lufs": best_metrics["lufs"],
        "truePeak": best_metrics["truePeak"],
        "durationSec": best_metrics["durationSec"],
        "passedChecks": best_metrics["passedChecks"],
    }
    entry["assets"] = {
        "wav": f"/assets/{entry_id}/out.wav",
        "mp3": f"/assets/{entry_id}/out.mp3",
        "spectrogram": f"/assets/{entry_id}/spectrogram.png",
        "code": f"/assets/{entry_id}/generate.py",
    }
    entry["notes"] = (
        ("Runner-verified synthesis (numpy). Prompt describes creative intent; code is executable."
         + shipped_note)
        if mock
        else entry.get("notes", "")
    )
    save_entry(entry_path, entry)

    # Optional MP3
    mp3_path = asset_dir / "out.mp3"
    try:
        import shutil
        import subprocess

        if shutil.which("ffmpeg"):
            subprocess.run(
                ["ffmpeg", "-y", "-i", str(wav_path), "-q:a", "4", str(mp3_path)],
                check=True,
                capture_output=True,
            )
    except Exception:
        pass

    return entry


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Opus Sound Directory generation")
    parser.add_argument("entry", type=Path, help="Path to content/entries/<id>.json")
    parser.add_argument("--mock", action="store_true", default=True, help="Mock synthesis (default)")
    parser.add_argument("--agent", action="store_true", help="Use Claude agent (not implemented)")
    parser.add_argument("--best-of", type=int, default=1, help="Run N times, keep best LUFS")
    args = parser.parse_args()

    mock = not args.agent
    result = run_entry(args.entry.resolve(), mock=mock, best_of=args.best_of)
    print(json.dumps(result["metrics"], indent=2))


if __name__ == "__main__":
    main()
