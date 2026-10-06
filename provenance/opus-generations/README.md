# Opus Sound Directory: real claude-opus-5-5 generations (PARTIAL, blocked)

Status (2026-10-06, 11:53 CT): **1 of 16 entries staged.** The Anthropic API account returned
`HTTP 400: Your credit balance is too low to access the Anthropic API` on the 3rd call and on every call after it.
The other 15 entries were never generated. Don't relabel them as Claude Opus.

Staged:
- `ui-success-chime/`: generate.py, out.wav (48 kHz stereo, 24000 frames), out.mp3, spectrogram.png,
  entry-patch.json, runs/ (API transcripts with the key redacted, plus usage, stdout and selection.json).
  Passed all checks: -14.0 LUFS, -3.9 dBTP, exact length, no DC or clipping. It is the only candidate
  (1 of 3 planned), so it was not picked from several. See runs/c1-result.json `note`: rounds 0 and 1 hit a
  host sandbox mount bug (not a model error). The unchanged round-0 code then passed when re-run in the
  fixed sandbox, with no extra API call.

For the coding agent: merge entry-patch.json into content/entries/<id>.json, **delete `targetModelId`**,
and copy generate.py, out.wav, out.mp3 and spectrogram.png to public/assets/<id>/.

To resume once credits are topped up (from the box):
    /workspace/.opus-venv/bin/python /workspace/opus-pipeline/pipeline.py   # skips finished candidates; cumulative tokens in /workspace/opus-work/tokens.json
    /workspace/.opus-venv/bin/python /workspace/opus-pipeline/stage.py
`_tooling/` holds copies of those scripts and the system prompt. They don't need to be committed.
