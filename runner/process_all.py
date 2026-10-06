#!/usr/bin/env python3
"""Run the verification pipeline on every content/entries/*.json."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from run import run_entry

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pipeline-only", action="store_true")
    parser.add_argument("--run-generate-py", action="store_true")
    parser.add_argument("--preserve-model-id", action="store_true")
    args = parser.parse_args()
    preserve = args.preserve_model_id or args.pipeline_only
    failed = []
    for entry_path in sorted((ROOT / "content" / "entries").glob("*.json")):
        try:
            run_entry(
                entry_path,
                mock=not args.pipeline_only,
                pipeline_only=args.pipeline_only,
                run_generate_py_flag=args.run_generate_py,
                preserve_model_id=preserve,
            )
        except Exception as exc:
            failed.append((entry_path.name, str(exc)))
    if failed:
        print(json.dumps({"failed": failed}, indent=2))
        sys.exit(1)
    print(json.dumps({"ok": True, "count": len(list((ROOT / "content" / "entries").glob("*.json")))}))


if __name__ == "__main__":
    main()
