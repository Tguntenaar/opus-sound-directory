"""Write runnable public/assets/<id>/generate.py from entry synth source."""

from __future__ import annotations

import inspect
import textwrap
from pathlib import Path

from synth import entry_synth

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_PATH = ROOT / "runner" / "templates" / "synth_runtime.py"


def write_generate_py(code_path: Path, entry: dict) -> None:
    entry_id = entry["id"]
    fn_name = entry_synth.REGISTRY[entry_id]
    fn = getattr(entry_synth, fn_name)
    fn_src = inspect.getsource(fn)
    helper_src = inspect.getsource(entry_synth._n) + "\n" + inspect.getsource(entry_synth._add)
    runtime = RUNTIME_PATH.read_text(encoding="utf-8")
    if runtime.startswith('"""'):
        end = runtime.find('"""', 3)
        runtime = runtime[end + 3 :].lstrip()
    if runtime.startswith("from __future__ import annotations"):
        runtime = runtime.split("\n", 1)[1].lstrip()
    duration = entry["timing"]["durationSec"]
    seed = entry.get("seed", 42)
    is_chaos = entry.get("category") == "chaos-calm"
    cue_helper = ""
    generate_call = f"    return {fn_name}({duration}, seed)"
    if is_chaos:
        cues = entry.get("cues") or []
        fps = entry.get("timing", {}).get("fps", 30)
        frame = cues[1]["frame"] if len(cues) > 1 else int(0.35 * duration * fps)
        cue_sample = int(frame / fps * 48000)
        generate_call = f"    cue = {cue_sample}\n    return {fn_name}({duration}, seed, cue)"

    constants = "E3, B3, D4, A3 = 164.81, 246.94, 293.66, 220.0\n"

    body = f'''"""Synthesis code for {entry_id}. Run: python generate.py (writes out.wav)."""
from __future__ import annotations

from pathlib import Path

import numpy as np

{runtime}

{constants}
{helper_src}
{fn_src}

def generate(seed: int = {seed}) -> np.ndarray:
{cue_helper}{generate_call}


if __name__ == "__main__":
    out = Path(__file__).resolve().parent / "out.wav"
    write_wav(out, generate())
    print(f"Wrote {{out}}")
'''
    code_path.parent.mkdir(parents=True, exist_ok=True)
    code_path.write_text(textwrap.dedent(body), encoding="utf-8")
