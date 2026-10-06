#!/usr/bin/env python3
"""
Opus Sound Directory runner.

Mock mode (default): per-entry numpy synthesis, executable generate.py, ffmpeg metrics.
Use --pipeline-only after dropping in external generate.py + out.wav (e.g. Claude Opus).
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
from entry_meta import apply_entry_meta
from mock_generate import write_wav
from pipeline import finish_entry_assets, run_generate_py
from synth.entry_synth import synthesise_for_entry

SAMPLE_RATE = 48000


def load_entry(entry_path: Path) -> dict:
    return json.loads(entry_path.read_text(encoding="utf-8"))


def save_entry(entry_path: Path, data: dict) -> None:
    entry_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def run_entry(
    entry_path: Path,
    mock: bool = True,
    best_of: int = 1,
    pipeline_only: bool = False,
    run_generate_py_flag: bool = False,
    preserve_model_id: bool = False,
) -> dict:
    entry = load_entry(entry_path)
    entry_id = entry["id"]
    timing = entry.get("timing", {})
    expected_samples = timing.get("samples")
    seed = int(entry.get("seed", 42))
    asset_dir = ROOT / "public" / "assets" / entry_id
    wav_path = asset_dir / "out.wav"
    spec_path = asset_dir / "spectrogram.png"
    code_path = asset_dir / "generate.py"
    mp3_path = asset_dir / "out.mp3"

    best_metrics = None
    best_seed = seed
    shipped_note = ""

    for attempt in range(best_of):
        attempt_seed = seed + attempt
        if pipeline_only:
            if run_generate_py_flag:
                run_generate_py(code_path)
            elif not wav_path.is_file():
                raise FileNotFoundError(f"pipeline-only: missing {wav_path}")
        elif mock:
            entry["seed"] = attempt_seed
            audio = synthesise_for_entry(entry)
            write_wav(wav_path, audio)
            write_generate_py(code_path, entry)
        else:
            raise NotImplementedError(
                "Agent mode not configured. Set ANTHROPIC_API_KEY and implement agent_generate(). "
                "See README for `claude -p` integration notes."
            )

        metrics, shipped_note = finish_entry_assets(
            entry,
            wav_path,
            spec_path,
            mp3_path,
            expected_samples=expected_samples,
        )
        expected_samples = entry["timing"].get("samples", expected_samples)

        if best_metrics is None or (metrics.get("lufs") or -70) > (best_metrics.get("lufs") or -70):
            best_metrics = metrics
            best_seed = attempt_seed

    if not pipeline_only:
        entry["seed"] = best_seed
    entry["generatedAt"] = date.today().isoformat()
    apply_entry_meta(entry, agent_mode=not mock, preserve_model_id=preserve_model_id or pipeline_only)
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
    if pipeline_only:
        if not entry.get("notes"):
            entry["notes"] = "Verified via runner pipeline (master, metrics, spectrogram, MP3)."
    elif mock:
        entry["notes"] = (
            "Runner-verified local numpy/scipy synthesis. "
            "Mastering: pyloudnorm stereo LUFS + true-peak limit (ffmpeg ebur128 verification)."
            + shipped_note
        )
    save_entry(entry_path, entry)
    return entry


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Opus Sound Directory generation")
    parser.add_argument("entry", type=Path, help="Path to content/entries/<id>.json")
    parser.add_argument("--mock", action="store_true", default=True, help="Mock synthesis (default)")
    parser.add_argument("--agent", action="store_true", help="Use Claude agent (not implemented)")
    parser.add_argument("--best-of", type=int, default=1, help="Run N times, keep best LUFS")
    parser.add_argument(
        "--pipeline-only",
        action="store_true",
        help="Skip local synth; master/verify/spectrogram/MP3 existing public/assets/<id>/out.wav",
    )
    parser.add_argument(
        "--run-generate-py",
        action="store_true",
        help="With --pipeline-only: execute public/assets/<id>/generate.py first",
    )
    parser.add_argument(
        "--preserve-model-id",
        action="store_true",
        help="Do not stamp modelId to local-synth (keep Opus modelId on ingested entries)",
    )
    args = parser.parse_args()

    mock = not args.agent and not args.pipeline_only
    preserve = args.preserve_model_id or args.pipeline_only
    result = run_entry(
        args.entry.resolve(),
        mock=mock,
        best_of=args.best_of,
        pipeline_only=args.pipeline_only,
        run_generate_py_flag=args.run_generate_py,
        preserve_model_id=preserve,
    )
    print(json.dumps(result["metrics"], indent=2))


if __name__ == "__main__":
    main()
