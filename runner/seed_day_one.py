#!/usr/bin/env python3
"""Create 16 day-one JSON entries and generate mock assets."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from run import run_entry

ENTRIES_DIR = ROOT / "content" / "entries"
MODEL_ID = "claude-opus-5-5"
GENERATED_AT = "2026-10-05"


def prompt_chaos(
    duration: int,
    fps: int,
    samples: int,
    bpm: int,
    chaos_desc: str,
    calm_desc: str,
    key: str,
    cues: list[tuple[int, str]],
) -> str:
    beat_frames = int(fps * 60 / bpm)
    cue_lines = "; ".join(f"frame {f} = {label}" for f, label in cues)
    return f"""Make a {duration} s music bed for a TikTok ad at {fps} fps.
Output: one WAV, 48 kHz / 16-bit / stereo, exactly {samples} samples.
Python + numpy/scipy only. Synthesise everything (no samples, no downloads). Fixed random seed.
Timing: {bpm} BPM (1 beat = {beat_frames} frames). Cues: {cue_lines}; last beat = soft ending that fades to exactly 0.
Sound: [chaos: {chaos_desc}] → [calm: {calm_desc}], key {key}.
Master: −14 LUFS integrated, true peak ≤ −1 dBTP.
You can't listen, so verify: measure loudness and peak with ffmpeg ebur128, check the exact length, confirm the energy change lands on each cue frame, check the notes fit the chords, render a spectrogram and inspect it. Fix and re-render until every check passes, then report the numbers."""


def sfx_prompt(kind: str, duration: float, samples: int, description: str) -> str:
    return f"""Make a {duration} s {kind} sound effect for video at 30 fps.
Output: one WAV, 48 kHz / 16-bit / stereo, exactly {samples} samples.
Python + numpy/scipy only. Synthesise everything (no samples, no downloads). Fixed random seed.
Sound: {description}
Master: −14 LUFS integrated, true peak ≤ −1 dBTP.
Verify length, loudness, peak with ffmpeg ebur128; render spectrogram; fix until checks pass."""


ENTRIES = [
    {
        "id": "chaos-calm-01",
        "title": "Chaos clocks → calm pad",
        "category": "chaos-calm",
        "tags": ["tiktok", "15s", "120bpm"],
        "duration": 15,
        "samples": 720000,
        "bpm": 120,
        "cues": [(0, "hit"), (150, "chaos stops, calm begins")],
        "prompt": prompt_chaos(
            15, 30, 720000, 120,
            "clashing clocks, notification pings, glitchy drums, rising noise",
            "warm maj9 pad, felt piano, soft half-time pulse",
            "D major",
            [(0, "hit"), (150, "chaos stops, calm begins")],
        ),
    },
    {
        "id": "chaos-calm-02",
        "title": "Traffic glitch → warm strings",
        "category": "chaos-calm",
        "tags": ["youtube", "30s", "90bpm"],
        "duration": 30,
        "samples": 1440000,
        "bpm": 90,
        "cues": [(0, "urban hit"), (300, "traffic cuts, strings swell")],
        "prompt": prompt_chaos(
            30, 30, 1440000, 90,
            "honks, sirens, stuttering hi-hats, bit-crushed noise",
            "slow legato strings, soft sub, gentle pulse at 90 BPM",
            "A minor",
            [(0, "urban hit"), (300, "traffic cuts, strings swell")],
        ),
    },
    {
        "id": "chaos-calm-03",
        "title": "Notification storm → breath",
        "category": "chaos-calm",
        "tags": ["podcast", "10s", "100bpm"],
        "duration": 10,
        "samples": 480000,
        "bpm": 100,
        "cues": [(0, "alert stack"), (120, "notifications mute")],
        "prompt": prompt_chaos(
            10, 30, 480000, 100,
            "stacked notification pings, rapid clicks, tense pulse",
            "airy pad, slow exhale noise bed, single soft bell",
            "F major",
            [(0, "alert stack"), (120, "notifications mute")],
        ),
    },
    {
        "id": "chaos-calm-04",
        "title": "Scroll frenzy → focus hum",
        "category": "chaos-calm",
        "tags": ["app", "8s", "110bpm"],
        "duration": 8,
        "samples": 384000,
        "bpm": 110,
        "cues": [(0, "swipe whoosh"), (90, "UI settles")],
        "prompt": prompt_chaos(
            8, 30, 384000, 110,
            "rapid UI ticks, swipe whooshes, bright digital chirps",
            "low focus hum, soft sine pulse, minimal reverb tail",
            "C major",
            [(0, "swipe whoosh"), (90, "UI settles")],
        ),
    },
    {
        "id": "chaos-calm-05",
        "title": "Storm cuts to sunrise",
        "category": "chaos-calm",
        "tags": ["documentary", "20s", "80bpm"],
        "duration": 20,
        "samples": 960000,
        "bpm": 80,
        "cues": [(0, "thunder hit"), (240, "rain stops")],
        "prompt": prompt_chaos(
            20, 30, 960000, 80,
            "thunder, wind gusts, rattling metal, noisy low drone",
            "bright morning pad, birds-like chirp synth, gentle 80 BPM kick",
            "G major",
            [(0, "thunder hit"), (240, "rain stops")],
        ),
    },
    {
        "id": "ad-bed-15-upbeat",
        "title": "15s upbeat retail pulse",
        "category": "ad-beds",
        "tags": ["ad", "15s", "128bpm"],
        "duration": 15,
        "samples": 720000,
        "bpm": 128,
        "cues": [(0, "logo hit"), (420, "outro tag")],
        "prompt": sfx_prompt(
            "upbeat ad bed",
            15,
            720000,
            "bright plucks, four-on-the-floor kick, claps on 2 and 4, key E major, energetic but not harsh; hit on frame 0, tag at frame 420.",
        ),
    },
    {
        "id": "ad-bed-30-lifestyle",
        "title": "30s lifestyle stroll",
        "category": "ad-beds",
        "tags": ["ad", "30s", "105bpm"],
        "duration": 30,
        "samples": 1440000,
        "bpm": 105,
        "cues": [(0, "intro hook"), (600, "brand moment")],
        "prompt": sfx_prompt(
            "lifestyle ad bed",
            30,
            1440000,
            "acoustic-guitar-like plucks (synthesised), soft shaker, warm bass, B major; gentle build to frame 600.",
        ),
    },
    {
        "id": "ad-bed-6-bumper",
        "title": "6s bumper sting",
        "category": "ad-beds",
        "tags": ["bumper", "6s", "140bpm"],
        "duration": 6,
        "samples": 288000,
        "bpm": 140,
        "cues": [(0, "hit"), (150, "resolve")],
        "prompt": sfx_prompt(
            "short ad bumper",
            6,
            288000,
            "punchy synth chord, tight kick, reverse cymbal into hit at frame 0, resolve by frame 150.",
        ),
    },
    {
        "id": "ad-bed-60-story",
        "title": "60s story arc bed",
        "category": "ad-beds",
        "tags": ["ad", "60s", "92bpm"],
        "duration": 60,
        "samples": 2880000,
        "bpm": 92,
        "cues": [(0, "cold open"), (900, "turn"), (1500, "cta")],
        "prompt": sfx_prompt(
            "narrative ad bed",
            60,
            2880000,
            "slow build: sparse piano-like tones, add pulse at frame 900, fuller harmony for CTA at frame 1500; D major.",
        ),
    },
    {
        "id": "drop-impact-heavy",
        "title": "Heavy impact drop",
        "category": "drops",
        "tags": ["drop", "3s"],
        "duration": 3,
        "samples": 144000,
        "bpm": 120,
        "cues": [(45, "impact")],
        "prompt": sfx_prompt(
            "transition drop",
            3,
            144000,
            "sub drop + noise burst + short tail; peak impact aligned to frame 45 at 30fps.",
        ),
    },
    {
        "id": "drop-whoosh-stinger",
        "title": "Whoosh into hit",
        "category": "drops",
        "tags": ["transition", "2s"],
        "duration": 2,
        "samples": 96000,
        "bpm": 120,
        "cues": [(30, "hit")],
        "prompt": sfx_prompt(
            "whoosh stinger",
            2,
            96000,
            "band-pass noise sweep up into metallic hit at frame 30.",
        ),
    },
    {
        "id": "riser-tension-8s",
        "title": "8s tension riser",
        "category": "risers",
        "tags": ["riser", "8s"],
        "duration": 8,
        "samples": 384000,
        "bpm": 120,
        "cues": [(210, "pre-drop swell")],
        "prompt": sfx_prompt(
            "riser",
            8,
            384000,
            "rising filtered noise + ascending sine stack; max energy frame 210 then cut.",
        ),
    },
    {
        "id": "ui-success-chime",
        "title": "Success chime",
        "category": "ui-sounds",
        "tags": ["ui", "0.5s"],
        "duration": 0.5,
        "samples": 24000,
        "bpm": 120,
        "cues": [(0, "chime")],
        "prompt": sfx_prompt(
            "UI success",
            0.5,
            24000,
            "two-tone pleasant chime, fast decay, no harsh highs; centre at frame 0.",
        ),
    },
    {
        "id": "ui-error-soft",
        "title": "Soft error tap",
        "category": "ui-sounds",
        "tags": ["ui", "0.4s"],
        "duration": 0.4,
        "samples": 19200,
        "bpm": 120,
        "cues": [(0, "tap")],
        "prompt": sfx_prompt(
            "UI error",
            0.4,
            19200,
            "low muted thud + short dissonant interval, non-alarming, frame 0.",
        ),
    },
    {
        "id": "logo-sting-bright",
        "title": "Bright logo sting",
        "category": "logo-stings",
        "tags": ["logo", "2.5s"],
        "duration": 2.5,
        "samples": 120000,
        "bpm": 120,
        "cues": [(0, "logo"), (60, "shimmer")],
        "prompt": sfx_prompt(
            "logo sting",
            2.5,
            120000,
            "major chord bloom + shimmer tail; logo at 0, sparkle at frame 60.",
        ),
    },
    {
        "id": "ambient-bed-lofi",
        "title": "Lo-fi ambient bed",
        "category": "ambient",
        "tags": ["ambient", "12s"],
        "duration": 12,
        "samples": 576000,
        "bpm": 75,
        "cues": [(0, "fade in")],
        "prompt": sfx_prompt(
            "ambient bed",
            12,
            576000,
            "warm detuned pads, subtle vinyl-like noise, very slow movement; loop-friendly fade in at 0.",
        ),
    },
]


def entry_json(spec: dict) -> dict:
    fps = 30
    duration = spec["duration"]
    samples = spec["samples"]
    return {
        "id": spec["id"],
        "slug": spec["id"],
        "title": spec["title"],
        "category": spec["category"],
        "tags": spec["tags"],
        "prompt": spec["prompt"],
        "modelId": MODEL_ID,
        "generatedAt": GENERATED_AT,
        "seed": 42,
        "timing": {
            "bpm": spec["bpm"],
            "fps": fps,
            "durationSec": duration,
            "samples": samples,
            "sampleRate": 48000,
        },
        "cues": [{"frame": f, "label": label} for f, label in spec["cues"]],
        "master": {"targetLufs": -14, "truePeakDbTp": -1},
        "metrics": {"lufs": None, "truePeak": None, "durationSec": None, "passedChecks": False},
        "assets": {
            "wav": f"/assets/{spec['id']}/out.wav",
            "mp3": f"/assets/{spec['id']}/out.mp3",
            "spectrogram": f"/assets/{spec['id']}/spectrogram.png",
            "code": f"/assets/{spec['id']}/generate.py",
        },
        "notes": "Placeholder until runner produces real assets.",
    }


def main() -> None:
    ENTRIES_DIR.mkdir(parents=True, exist_ok=True)
    for spec in ENTRIES:
        path = ENTRIES_DIR / f"{spec['id']}.json"
        path.write_text(json.dumps(entry_json(spec), indent=2) + "\n", encoding="utf-8")
        print(f"Seeded {path.name}")
        run_entry(path, mock=True, best_of=1)
    print("Done: 16 entries with assets.")


if __name__ == "__main__":
    main()
