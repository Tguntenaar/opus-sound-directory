#!/usr/bin/env python3
"""Measure loudness for every shipped asset and optional take MP3s; write CSV report."""

from __future__ import annotations

import argparse
import csv
import json
import sys
import wave
from datetime import date
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from loudness_policy import check_loudness_metrics, expected_integrated_lufs, load_targets_config
from verify import ffmpeg_ebur128

DEFAULT_OUT = ROOT / "docs" / "audits" / "loudness-report.csv"


def pcm_sample_peak_db(path: Path) -> float | None:
    try:
        with wave.open(str(path), "rb") as wf:
            frames = wf.readframes(wf.getnframes())
        samples = np.frombuffer(frames, dtype=np.int16).astype(np.float64) / 32768.0
        peak = float(np.max(np.abs(samples)))
        if peak <= 0:
            return None
        return 20.0 * np.log10(peak)
    except wave.Error:
        return None


def iter_audio_files(include_takes: bool) -> list[tuple[str, str, Path]]:
    """Return (entry_id, role, path) rows."""
    rows: list[tuple[str, str, Path]] = []
    assets = ROOT / "public" / "assets"
    for entry_path in sorted((ROOT / "content" / "entries").glob("*.json")):
        entry = json.loads(entry_path.read_text(encoding="utf-8"))
        eid = entry["id"]
        base = assets / eid
        for name, role in (("out.wav", "wav"), ("out.mp3", "mp3")):
            p = base / name
            if p.is_file():
                rows.append((eid, role, p))
        if include_takes:
            takes_dir = base / "takes"
            if takes_dir.is_dir():
                for take in sorted(takes_dir.glob("*.mp3")):
                    rows.append((eid, f"take:{take.stem}", take))
    return rows


def audit_row(entry: dict, role: str, path: Path) -> dict:
    m = ffmpeg_ebur128(path)
    pcm_peak = pcm_sample_peak_db(path) if path.suffix.lower() == ".wav" else None
    clipped = pcm_peak is not None and pcm_peak > -0.1
    metrics = {
        "lufs": m.get("lufs"),
        "truePeak": m.get("truePeak"),
        "lufsMomentaryMax": m.get("lufsMomentaryMax"),
    }
    ok, reasons = check_loudness_metrics(entry, metrics)
    target = expected_integrated_lufs(entry)
    return {
        "entry_id": entry["id"],
        "category": entry.get("category", ""),
        "role": role,
        "path": str(path.relative_to(ROOT)),
        "target_lufs": f"{target:.1f}",
        "integrated_lufs": "" if m.get("lufs") is None else f"{m['lufs']:.2f}",
        "momentary_max_lufs": ""
        if m.get("lufsMomentaryMax") is None
        else f"{m['lufsMomentaryMax']:.2f}",
        "true_peak_dbtp": "" if m.get("truePeak") is None else f"{m['truePeak']:.2f}",
        "pcm_peak_dbfs": "" if pcm_peak is None else f"{pcm_peak:.2f}",
        "clipped_pcm": "yes" if clipped else "no",
        "pass": "yes" if ok else "no",
        "notes": "; ".join(reasons),
    }


def write_csv(rows: list[dict], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else []
    with out_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit catalog loudness (LUFS / true peak)")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=DEFAULT_OUT,
        help=f"CSV path (default: {DEFAULT_OUT.relative_to(ROOT)})",
    )
    parser.add_argument("--takes", action="store_true", help="Include public/assets/*/takes/*.mp3")
    parser.add_argument("--check", action="store_true", help="Exit 1 if any row fails")
    args = parser.parse_args()

    load_targets_config()
    entries = {
        p.stem: json.loads(p.read_text(encoding="utf-8"))
        for p in (ROOT / "content" / "entries").glob("*.json")
    }
    out_rows: list[dict] = []
    failures = 0
    for eid, role, path in iter_audio_files(args.takes):
        row = audit_row(entries[eid], role, path)
        out_rows.append(row)
        if row["pass"] != "yes":
            failures += 1

    write_csv(out_rows, args.output)
    summary_path = args.output.with_name("loudness-summary.md")
    summary_path.write_text(
        "\n".join(
            [
                f"# Loudness audit ({date.today().isoformat()})",
                "",
                f"Rows: {len(out_rows)}. Failures: {failures}.",
                f"Policy: [`config/loudness-targets.json`](../config/loudness-targets.json).",
                f"Full table: [`{args.output.name}`](./{args.output.name}).",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(json.dumps({"output": str(args.output), "rows": len(out_rows), "failures": failures}))
    if args.check and failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
