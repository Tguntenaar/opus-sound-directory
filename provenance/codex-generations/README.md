# Codex generation candidates

The `hero8/` collection contains three takes for each of nine sound briefs, authored with OpenAI Codex and synthesized locally using NumPy/SciPy. No Anthropic API or recorded samples were used.

**Status: awaiting listening selection.** These are review candidates. No catalog entries or production assets have been replaced, and no take is marked as a winner. Attribution is Codex, not Claude Opus.

## Review

Open [`hero8/index.html`](./hero8/index.html) from a local checkout to compare all 27 WAVs. See [`hero8/REPORT.md`](./hero8/REPORT.md) for measurements, visual QA, limitations and provisional rankings. Rankings have not been confirmed by listening.

Each sound folder contains `take-1.py` through `take-3.py`, corresponding 48 kHz stereo PCM16 WAVs, spectrograms and meter logs. Each script runs independently:

```sh
python3 provenance/codex-generations/hero8/game-coin-pickup/take-2.py /tmp/coin.wav
```

Dependencies: Python, NumPy and SciPy. FFmpeg provides additional loudness verification when installed. Matplotlib is only needed to regenerate spectrograms.

To verify the collection or rebuild its ZIP:

```sh
python3 provenance/codex-generations/hero8/verify_collection.py
python3 provenance/codex-generations/hero8/package_collection.py
```

The packager writes `provenance/codex-generations/hero8.zip`, ignored by Git. Source files and individual assets are tracked instead. The original delivery ZIP is reproducible from this directory.

After selecting winners, record them in `hero8/selection.json` and integrate them through the normal catalog workflow with accurate model attribution. Until then this archive remains outside `public/` and `content/entries/`.
