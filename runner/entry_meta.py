"""Per-entry mood/tempo defaults and model stamping for the runner."""

from __future__ import annotations

LOCAL_SYNTH_MODEL_ID = "local-synth"
TARGET_OPUS_MODEL_ID = "claude-opus-4-20250514"

ENTRY_MOOD: dict[str, dict] = {
    "ad-bed-15-upbeat": {
        "mood": ["upbeat", "happy", "energetic", "bright"],
        "tempo": "fast",
    },
    "ad-bed-6-bumper": {
        "mood": ["upbeat", "energetic", "bright"],
        "tempo": "fast",
    },
    "ad-bed-30-lifestyle": {
        "mood": ["calm", "happy", "bright"],
        "tempo": "medium",
    },
    "ad-bed-60-story": {
        "mood": ["slow", "sad", "calm", "dark"],
        "tempo": "slow",
    },
    "chaos-calm-01": {
        "mood": ["energetic", "dark", "calm", "bright"],
        "tempo": "fast",
    },
    "chaos-calm-02": {
        "mood": ["energetic", "dark", "sad", "calm"],
        "tempo": "medium",
    },
    "chaos-calm-03": {
        "mood": ["energetic", "dark", "calm"],
        "tempo": "medium",
    },
    "chaos-calm-04": {
        "mood": ["upbeat", "energetic", "calm", "happy"],
        "tempo": "fast",
    },
    "chaos-calm-05": {
        "mood": ["energetic", "dark", "calm", "sad"],
        "tempo": "medium",
    },
    "drop-impact-heavy": {
        "mood": ["energetic", "dark"],
        "tempo": "fast",
    },
    "drop-whoosh-stinger": {
        "mood": ["energetic", "bright"],
        "tempo": "fast",
    },
    "logo-sting-bright": {
        "mood": ["happy", "bright", "upbeat"],
        "tempo": "fast",
    },
    "riser-tension-8s": {
        "mood": ["energetic", "dark"],
        "tempo": "medium",
    },
    "ui-success-chime": {
        "mood": ["happy", "bright"],
        "tempo": "fast",
    },
    "ui-error-soft": {
        "mood": ["sad", "calm", "dark"],
        "tempo": "slow",
    },
    "ambient-bed-lofi": {
        "mood": ["slow", "calm", "sad", "dark"],
        "tempo": "slow",
    },
}


def apply_entry_meta(entry: dict, agent_mode: bool = False) -> None:
    entry_id = entry["id"]
    meta = ENTRY_MOOD.get(entry_id, {})
    if meta:
        entry["mood"] = meta.get("mood", entry.get("mood", []))
        if "tempo" in meta:
            entry["tempo"] = meta["tempo"]
    if agent_mode:
        entry["modelId"] = TARGET_OPUS_MODEL_ID
        entry.pop("targetModelId", None)
    else:
        entry["modelId"] = LOCAL_SYNTH_MODEL_ID
        entry["targetModelId"] = TARGET_OPUS_MODEL_ID
