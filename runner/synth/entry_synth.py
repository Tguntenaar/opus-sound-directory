"""Per-entry synthesis — each id has a distinct render tuned to its JSON prompt."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "runner" / "templates"))
from synth_runtime import (  # noqa: E402
    SAMPLE_RATE,
    bass,
    bandpass_noise,
    chaos_clocks,
    chaos_traffic,
    clap,
    crossfade_at,
    fade_edges,
    hihat,
    kick,
    master_chain,
    metallic_hit,
    pad_layers,
    piano_tone,
    pluck,
    stereo,
    ui_chime_pair,
    whoosh_riser,
)

# E major / B major / D major / A minor roots (Hz)
E3, B3, D4, A3 = 164.81, 246.94, 293.66, 220.0


def _n(duration: float) -> int:
    return int(SAMPLE_RATE * duration)


def _add(mono: np.ndarray, pos: int, snippet: np.ndarray, gain: float = 1.0) -> None:
    end = min(len(mono), pos + len(snippet))
    if pos >= end:
        return
    mono[pos:end] += snippet[: end - pos] * gain


def _cue_frame(entry: dict, index: int = 1) -> int:
    cues = entry.get("cues") or []
    fps = float(entry.get("timing", {}).get("fps", 30))
    if len(cues) <= index:
        return int(0.35 * _n(float(entry["timing"]["durationSec"])))
    return int(cues[index]["frame"] / fps * SAMPLE_RATE)


def synth_ad_bed_15_upbeat(duration: float, seed: int) -> np.ndarray:
    bpm = 128
    beat = int(SAMPLE_RATE * 60 / bpm)
    n = _n(duration)
    mono = np.zeros(n, dtype=np.float32)
    progression = [329.63, 392.0, 440.0, 369.99]  # E4 G4 A4 F#4
    bar = beat * 4
    for i in range(0, n, beat):
        if i % beat == 0:
            _add(mono, i, kick(0.14, seed=seed + i), 0.75)
        if i % beat == beat // 2:
            _add(mono, i, hihat(0.05, seed=seed + i), 0.35)
        if i % (beat * 2) == beat:
            _add(mono, i, clap(0.1, seed=seed + i), 0.55)
    for bar_i, start in enumerate(range(0, n, bar)):
        note = progression[bar_i % len(progression)]
        p = pluck(note, min(0.35, duration), seed=seed + bar_i)
        _add(mono, start, p, 0.45)
    mono += bass(E3 / 2, duration) * 0.35
    tag = int(14 * SAMPLE_RATE)
    if tag < n:
        _add(mono, tag, pluck(659.25, 0.4, seed=seed), 0.5)
    return stereo(master_chain(mono))


def synth_ad_bed_6_bumper(duration: float, seed: int) -> np.ndarray:
    bpm = 140
    beat = int(SAMPLE_RATE * 60 / bpm)
    n = _n(duration)
    mono = np.zeros(n, dtype=np.float32)
    for i in range(0, n, beat):
        _add(mono, i, kick(0.12, seed=seed + i), 0.8)
        if i % (beat * 2) == beat:
            _add(mono, i, clap(0.08, seed=seed), 0.5)
    hook = pluck(523.25, 0.25, seed=seed)
    _add(mono, 0, hook, 0.7)
    mono += bass(98.0, duration) * 0.4
    return stereo(master_chain(mono))


def synth_ad_bed_30_lifestyle(duration: float, seed: int) -> np.ndarray:
    bpm = 105
    beat = int(SAMPLE_RATE * 60 / bpm)
    n = _n(duration)
    mono = np.zeros(n, dtype=np.float32)
    chords = [493.88, 622.25, 739.99, 587.33]  # B major colours
    for i in range(0, n, beat):
        if i % beat == 0:
            _add(mono, i, kick(0.11, seed=seed), 0.45)
        if i % (beat // 2) == 0:
            _add(mono, i, hihat(0.04, seed=seed + i), 0.22)
    for bi, start in enumerate(range(0, n, beat * 4)):
        note = chords[bi % len(chords)]
        p = pluck(note, 0.28, seed=seed + bi)
        _add(mono, start, p, 0.38)
    mono += bass(B3 / 2, duration) * 0.32
    build = int(20 * SAMPLE_RATE)
    if build < n:
        mono[build:] += pad_layers(B3, duration - 20, seed=seed) * np.linspace(0, 0.35, n - build)
    return stereo(master_chain(mono))


def synth_ad_bed_60_story(duration: float, seed: int) -> np.ndarray:
    n = _n(duration)
    mono = np.zeros(n, dtype=np.float32)
    notes = [293.66, 329.63, 369.99, 440.0, 493.88]
    spacing = int(3.5 * SAMPLE_RATE)
    for i, start in enumerate(range(0, n, spacing)):
        tone = piano_tone(notes[i % len(notes)], 1.2, seed=seed + i)
        end = min(n, start + len(tone))
        mono[start:end] += tone[: end - start] * 0.42
    pulse_at = int(30 * SAMPLE_RATE)
    for i in range(pulse_at, n, int(SAMPLE_RATE * 60 / 92)):
        k = kick(0.1, seed=seed + i)
        end = min(n, i + len(k))
        mono[i:end] += k[: end - i] * 0.35
    cta = int(50 * SAMPLE_RATE)
    if cta < n:
        mono[cta:] += pad_layers(D4, duration - 50, seed=seed) * np.linspace(0, 0.45, n - cta)
    mono += bass(D4 / 2, duration) * 0.25
    return stereo(master_chain(mono))


def synth_chaos_calm_01(duration: float, seed: int, cue_sample: int) -> np.ndarray:
    chaos = chaos_clocks(duration * 0.4, seed=seed)
    chaos = np.pad(chaos, (0, max(0, _n(duration) - len(chaos))))[: _n(duration)]
    calm = pad_layers(D4, duration, seed=seed + 99) + bass(D4 / 2, duration) * 0.4
    _add(calm, int(0.5 * SAMPLE_RATE), pluck(440, 0.5, seed=seed), 0.15)
    return stereo(master_chain(crossfade_at(chaos, calm, cue_sample)))


def synth_chaos_calm_02(duration: float, seed: int, cue_sample: int) -> np.ndarray:
    chaos = chaos_traffic(duration * 0.45, seed=seed)
    chaos = np.pad(chaos, (0, max(0, _n(duration) - len(chaos))))[: _n(duration)]
    calm = pad_layers(A3, duration, seed=seed) * 0.9
    calm += bass(A3 / 2, duration) * 0.35
    return stereo(master_chain(crossfade_at(chaos, calm, cue_sample, xfade_sec=0.5)))


def synth_chaos_calm_03(duration: float, seed: int, cue_sample: int) -> np.ndarray:
    n = _n(duration)
    chaos = bandpass_noise(duration * 0.35, 200, 6000, seed=seed) * 0.5
    chaos = np.pad(chaos, (0, max(0, n - len(chaos))))[:n]
    for i in range(0, len(chaos), int(0.25 * SAMPLE_RATE)):
        _add(chaos, i, kick(0.08, seed=seed + i), 0.6)
    calm = pad_layers(277.18, duration, seed=seed)  # C# context
    return stereo(master_chain(crossfade_at(chaos, calm, cue_sample)))


def synth_chaos_calm_04(duration: float, seed: int, cue_sample: int) -> np.ndarray:
    n = _n(duration)
    chaos = np.zeros(n, dtype=np.float32)
    for i in range(0, n, int(0.18 * SAMPLE_RATE)):
        _add(chaos, i, hihat(0.04, seed=seed + i), 0.7)
        _add(chaos, i, kick(0.07, seed=seed), 0.4)
    calm = pad_layers(329.63, duration, seed=seed)
    _add(calm, int(1.0 * SAMPLE_RATE), pluck(392, 0.6, seed=seed), 0.2)
    return stereo(master_chain(crossfade_at(chaos, calm, cue_sample, xfade_sec=0.25)))


def synth_chaos_calm_05(duration: float, seed: int, cue_sample: int) -> np.ndarray:
    n = _n(duration)
    chaos = chaos_clocks(duration * 0.3, seed=seed) + bandpass_noise(duration * 0.3, 500, 9000, seed=seed + 3) * 0.35
    chaos = np.pad(chaos, (0, max(0, n - len(chaos))))[:n]
    calm = pad_layers(349.23, duration, seed=seed) + bass(174.61, duration) * 0.35
    return stereo(master_chain(crossfade_at(chaos, calm, cue_sample, xfade_sec=0.45)))


def synth_drop_impact_heavy(duration: float, seed: int) -> np.ndarray:
    n = _n(duration)
    mono = np.zeros(n, dtype=np.float32)
    hit = int(0.55 * n)
    tail = n - hit
    k = kick(0.45, seed=seed)
    k = np.pad(k, (0, max(0, tail - len(k))))[:tail]
    mono[hit:] += k * np.linspace(1, 0.2, tail)
    mono[:hit] += whoosh_riser(duration * 0.55, seed=seed)[:hit] * 0.35
    _add(mono, hit, metallic_hit(seed=seed), 0.65)
    return stereo(master_chain(mono, target_lufs=-12.0))


def synth_drop_whoosh_stinger(duration: float, seed: int) -> np.ndarray:
    n = _n(duration)
    mono = np.zeros(n, dtype=np.float32)
    hit_frame = int(1.0 * SAMPLE_RATE)
    mono[:hit_frame] += whoosh_riser(1.0, seed=seed) * np.linspace(0.2, 1, hit_frame)
    hit = metallic_hit(seed=seed + 1)
    _add(mono, hit_frame, hit, 0.8)
    _add(mono, hit_frame + len(hit), kick(0.25, seed=seed), 0.3)
    return stereo(master_chain(mono, target_lufs=-12.0))


def synth_logo_sting_bright(duration: float, seed: int) -> np.ndarray:
    n = _n(duration)
    mono = np.zeros(n, dtype=np.float32)
    chord = [523.25, 659.25, 783.99]
    for i, f in enumerate(chord):
        bloom = pluck(f, min(1.2, duration), seed=seed + i)
        mono[: len(bloom)] += bloom * (0.55 - i * 0.08)
    sparkle_at = int(2.0 * SAMPLE_RATE)
    if sparkle_at < n:
        s = pluck(1318.5, 0.35, seed=seed + 9)
        _add(mono, sparkle_at, s, 0.45)
    return stereo(master_chain(fade_edges(mono, 0.02)))


def synth_riser_tension_8s(duration: float, seed: int) -> np.ndarray:
    mono = whoosh_riser(duration, seed=seed)
    n = len(mono)
    sub = np.sin(2 * np.pi * np.cumsum(np.linspace(40, 120, n)) / SAMPLE_RATE) * np.linspace(0, 0.35, n)
    mono = (mono + sub.astype(np.float32)).astype(np.float32)
    return stereo(master_chain(mono, target_lufs=-10.0))


def synth_ui_success_chime(duration: float, seed: int) -> np.ndarray:
    mono = ui_chime_pair(880, 1174.66, duration, seed=seed)
    return stereo(master_chain(mono))


def synth_ui_error_soft(duration: float, seed: int) -> np.ndarray:
    mono = ui_chime_pair(420, 330, duration, seed=seed) * 0.85
    mono += bandpass_noise(duration, 200, 800, seed=seed) * 0.08
    return stereo(master_chain(mono))


def synth_ambient_bed_lofi(duration: float, seed: int) -> np.ndarray:
    mono = pad_layers(220, duration, seed=seed) * 0.55
    mono += pad_layers(277.18, duration, seed=seed + 1) * 0.35
    _add(mono, int(2.5 * SAMPLE_RATE), pluck(440, 0.8, seed=seed), 0.08)
    return stereo(master_chain(mono, target_lufs=-16.0))


REGISTRY: dict[str, str] = {
    "ad-bed-15-upbeat": "synth_ad_bed_15_upbeat",
    "ad-bed-6-bumper": "synth_ad_bed_6_bumper",
    "ad-bed-30-lifestyle": "synth_ad_bed_30_lifestyle",
    "ad-bed-60-story": "synth_ad_bed_60_story",
    "chaos-calm-01": "synth_chaos_calm_01",
    "chaos-calm-02": "synth_chaos_calm_02",
    "chaos-calm-03": "synth_chaos_calm_03",
    "chaos-calm-04": "synth_chaos_calm_04",
    "chaos-calm-05": "synth_chaos_calm_05",
    "drop-impact-heavy": "synth_drop_impact_heavy",
    "drop-whoosh-stinger": "synth_drop_whoosh_stinger",
    "logo-sting-bright": "synth_logo_sting_bright",
    "riser-tension-8s": "synth_riser_tension_8s",
    "ui-success-chime": "synth_ui_success_chime",
    "ui-error-soft": "synth_ui_error_soft",
    "ambient-bed-lofi": "synth_ambient_bed_lofi",
}


def synthesise_for_entry(entry: dict) -> np.ndarray:
    entry_id = entry["id"]
    duration = float(entry["timing"]["durationSec"])
    seed = int(entry.get("seed", 42))
    fn_name = REGISTRY.get(entry_id)
    if not fn_name:
        raise KeyError(f"No synth for {entry_id}")
    fn = globals()[fn_name]
    if entry.get("category") == "chaos-calm":
        cue = _cue_frame(entry, 1)
        return fn(duration, seed, cue)
    return fn(duration, seed)
