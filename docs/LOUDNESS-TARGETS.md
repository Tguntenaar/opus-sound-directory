# Loudness targets (Opus Sounds Directory)

Every shipped file (`public/assets/<id>/out.wav`, `out.mp3`, and hero8 `takes/*.mp3` when present) is checked against these rules. Machine-readable policy: [`config/loudness-targets.json`](../config/loudness-targets.json).

## True peak

- **Ceiling: −1.0 dBTP** (ffmpeg `ebur128=peak=true` on the served file).
- No PCM clipping on shipped WAVs (sample peak ≤ −0.1 dBFS).

## Integrated loudness by profile

| Profile | When | Integrated LUFS | Tolerance |
|--------|------|-----------------|-----------|
| **Program** | Most categories (beds, ambient, drops, risers, stings, meme, retro, guitar, gaming, …) | **−14.0** | ±0.5 LU |
| **UI quiet** | `ui-sounds` under ~1.05 s (one-shots) | **−17.0** | ±0.5 LU integrated, or ±1.0 LU on **momentary max** when duration &lt; 0.4 s |
| **UI sprite** | `ui-sounds` longer sprites (coin kit, cozy UI, fishing minigame, …) | **−17.0** | ±0.5 LU |
| **Override** | `metric-counter-flash-ticks` | **−14.0** | per brief (3 s dashboard counter) |

Per-entry `master.targetLufs` in `content/entries/*.json` wins over category defaults when set.

## Why UI is quieter

Short clicks and chimes sound much louder than a −14 LUFS bed when you scrub the catalog. One-shots and UI sprites target **−17 LUFS** so level matches when browsing; long beds and music stay at **−14 LUFS** (podcast/broadcast-style).

## Running the audit

```bash
pip install -r runner/requirements.txt   # numpy, scipy; ffmpeg on PATH
node scripts/loudness-audit.mjs          # writes docs/audits/loudness-report.csv
node scripts/loudness-audit.mjs --check  # non-zero exit if anything fails
node scripts/loudness-audit.mjs --takes  # include take-voting MP3s
```

`npm test` includes `lib/loudness-catalog.test.ts`, which re-measures every catalog MP3 against this policy (requires ffmpeg).

## Remastering outliers

```bash
python3 runner/run.py content/entries/<id>.json --pipeline-only --preserve-model-id
```

The pipeline loudness-normalises from the 48 kHz `masters/<id>/out.wav` when present, re-encodes MP3, downsamples oversized WAVs for Workers, and refreshes spectrograms and `metrics` in the entry JSON.
