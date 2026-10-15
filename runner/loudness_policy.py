"""Catalog loudness targets (shared with config/loudness-targets.json)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "loudness-targets.json"


def load_targets_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def _profile_matches(entry: dict, profile: dict) -> bool:
    eid = entry.get("id", "")
    if eid in profile.get("excludeEntryIds", []):
        return False
    cat = entry.get("category", "")
    if cat not in profile.get("categories", []):
        return False
    dur = float(entry.get("timing", {}).get("durationSec", 999))
    if "maxDurationSec" in profile and dur > float(profile["maxDurationSec"]):
        return False
    if "minDurationSec" in profile and dur < float(profile["minDurationSec"]):
        return False
    return True


def expected_integrated_lufs(entry: dict, config: dict[str, Any] | None = None) -> float:
    config = config or load_targets_config()
    overrides = config.get("entryOverrides", {})
    eid = entry.get("id", "")
    if eid in overrides and "integratedLufs" in overrides[eid]:
        return float(overrides[eid]["integratedLufs"])
    master = entry.get("master") or {}
    if master.get("targetLufs") is not None:
        return float(master["targetLufs"])
    for profile in config.get("profiles", []):
        if _profile_matches(entry, profile):
            return float(profile["integratedLufs"])
    return float(config.get("defaultIntegratedLufs", -14.0))


def true_peak_ceiling(_entry: dict, config: dict[str, Any] | None = None) -> float:
    config = config or load_targets_config()
    return float(config["truePeakDbTpMax"])


def uses_momentary_loudness(entry: dict, config: dict[str, Any] | None = None) -> bool:
    config = config or load_targets_config()
    dur = float(entry.get("timing", {}).get("durationSec", 999))
    return dur < float(config.get("useMomentaryWhenDurationBelowSec", 0.4))


def check_loudness_metrics(
    entry: dict,
    metrics: dict[str, float | None],
    config: dict[str, Any] | None = None,
) -> tuple[bool, list[str]]:
    """Return (ok, reasons). metrics: lufs, truePeak, optional lufsMomentaryMax."""
    config = config or load_targets_config()
    reasons: list[str] = []
    target = expected_integrated_lufs(entry, config)
    peak_ceiling = true_peak_ceiling(entry, config)
    peak = metrics.get("truePeak")
    if peak is None:
        reasons.append("missing true peak")
    elif peak > peak_ceiling + 0.05:
        reasons.append(f"true peak {peak:.2f} dBTP > {peak_ceiling:.2f}")

    lufs = metrics.get("lufs")
    momentary = metrics.get("lufsMomentaryMax")
    if uses_momentary_loudness(entry, config) and momentary is not None:
        tol = float(config.get("momentaryToleranceLu", 1.0))
        if abs(momentary - target) > tol:
            reasons.append(f"momentary max {momentary:.2f} LUFS vs target {target:.2f}")
    elif lufs is None:
        reasons.append("missing integrated LUFS")
    else:
        tol = float(config.get("integratedToleranceLu", 0.5))
        if abs(lufs - target) > tol:
            reasons.append(f"integrated {lufs:.2f} LUFS vs target {target:.2f}")

    return (len(reasons) == 0, reasons)
