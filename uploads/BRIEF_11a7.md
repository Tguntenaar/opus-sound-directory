# Opus Sound Directory — MVP brief

Build the first version of a directory of Claude Opus–generated audio (inspired by cursor.directory’s *idea*, not its code — that repo has no license).

## Product

A browsable site of sound entries. Each entry must show:
- the prompt
- an audio player (actual result WAV/MP3)
- the generated Python code
- a spectrogram image
- measured numbers: loudness (LUFS), true peak (dBTP), length (samples/seconds)
- model ID (e.g. `claude-opus-5-5`) and run date

Categories:
- ad beds by length
- drops and transitions
- chaos → calm
- risers
- UI and app sounds
- logo stings
- ambient beds

Be upfront on the site: sounds are synthesised (precise, royalty-free, video-timed) but not realistic instruments/vocals; taste still needs a human ear.

## Entry format (JSON in git for v1)

Store entries as JSON under `content/entries/*.json` (one file per entry). Suggested schema:

```json
{
  "id": "chaos-calm-01",
  "slug": "chaos-calm-01",
  "title": "Chaos clocks → calm pad",
  "category": "chaos-calm",
  "tags": ["tiktok", "15s", "120bpm"],
  "prompt": "...full prompt text...",
  "modelId": "claude-opus-5-5",
  "generatedAt": "2026-10-05",
  "seed": 42,
  "timing": { "bpm": 120, "fps": 30, "durationSec": 15, "samples": 720000, "sampleRate": 48000 },
  "cues": [{ "frame": 0, "label": "hit" }, { "frame": 150, "label": "chaos stops, calm begins" }],
  "master": { "targetLufs": -14, "truePeakDbTp": -1 },
  "metrics": { "lufs": null, "truePeak": null, "durationSec": null, "passedChecks": false },
  "assets": {
    "wav": "/assets/chaos-calm-01/out.wav",
    "mp3": "/assets/chaos-calm-01/out.mp3",
    "spectrogram": "/assets/chaos-calm-01/spectrogram.png",
    "code": "/assets/chaos-calm-01/generate.py"
  },
  "notes": "Placeholder until runner produces real assets."
}
```

Ship **16 day-one entry stubs** with realistic prompts filled in (5 chaos→calm, 4 upbeat/ad beds, 7 SFX: drops/risers/UI/logo/ambient). Use the prompt template below. Real audio/code/spectrograms can be placeholders (silent short WAV or “coming soon” UI) if generation isn’t available in this environment — but the schema, paths, and UI must be complete.

### Prompt template (fill brackets)

```
Make a [15] s music bed for a [TikTok ad] at [30] fps.
Output: one WAV, 48 kHz / 16-bit / stereo, exactly [720000] samples.
Python + numpy/scipy only. Synthesise everything (no samples, no downloads). Fixed random seed.
Timing: [120] BPM (1 beat = [15] frames). Cues: frame [0] = [hit]; frame [150] = [chaos stops, calm begins]; last beat = soft ending that fades to exactly 0.
Sound: [chaos: clashing clocks, notification pings, glitchy drums, rising noise] → [calm: warm maj9 pad, felt piano, soft half-time pulse], key [D major].
Master: −14 LUFS integrated, true peak ≤ −1 dBTP.
You can't listen, so verify: measure loudness and peak with ffmpeg ebur128, check the exact length, confirm the energy change lands on each cue frame, check the notes fit the chords, render a spectrogram and inspect it. Fix and re-render until every check passes, then report the numbers.
```

Good prompts are specific and numeric: output contract, timing grid tied to video frames, plain-language sound description (styles not artist names), mastering targets, self-check with ffmpeg.

## Runner (`runner/`)

Python tooling that:
1. Takes an entry prompt + seed
2. (Optionally) calls Claude headless / Agent SDK — if API keys aren’t available, implement the interface and a **mock mode** that writes a short synthesised placeholder WAV with numpy and fills metrics
3. Runs verification: length, LUFS/peak via ffmpeg when available, spectrogram render
4. Writes assets into `public/assets/<id>/` and updates the entry JSON metrics
5. Supports “run 3 times, keep best by metrics” as a flag (even if mock only runs once)

Include a small shared starter lib sketch (`runner/lib/` or `shared/audio_lib/`) documenting drums/synths/reverb/limiter hooks — doesn’t need 2500 lines; a clean stub with the intended API is enough for MVP.

Document how to point at real `claude -p` / Agent SDK later in README.

## Site

Next.js app targeting **Cloudflare Workers via vinext** (`create-vinext-app` Cloudflare target preferred; if vinext bootstrap is awkward, plain Next.js App Router with clear Cloudflare/R2 notes is OK).

Pages:
- Home: browse by category, cards with play button + title + category
- Entry detail: player, prompt, code viewer, spectrogram, metrics, model/date, copy-prompt button
- About: synthesised / royalty-free disclaimer
- Simple submit form UI (can POST to nowhere / store as TODO — no DB yet; JSON-in-git is the source of truth)

Nice UX: copy button for prompts, keyboard-friendly player, dark clean directory aesthetic (do **not** copy cursor.directory code or assets).

Audio files: put placeholders under `public/assets/...`. R2 can come later; note it in README.

## Deliverables (done when)

1. Repo builds (`npm install && npm run build` or vinext equivalent)
2. `content/entries/` has 16 JSON entries with filled prompts across categories
3. Entry detail pages render all required fields
4. Runner package with mock generate + verify path documented
5. README: concept, how to add an entry, how to run the runner, Cloudflare deploy notes, R2 later
6. No dependency on cursor/community-plugins code

## Out of scope for this run

- Live Claude API calls requiring secrets (mock is fine)
- Real X/Twitter posting
- Database / user auth / voting backend (UI affordances OK as stubs)
