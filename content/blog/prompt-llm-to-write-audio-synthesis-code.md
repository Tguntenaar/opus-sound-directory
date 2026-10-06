---
title: "How to Prompt an LLM to Write Code That Generates Sound (Python and Web Audio)"
slug: "prompt-llm-to-write-audio-synthesis-code"
description: "How to get Claude or another LLM to write numpy/scipy or Web Audio code that renders sound effects with exact length, cue timing and loudness."
date: "2026-10-06"
keywords: ["generate sound with python", "LLM audio synthesis code", "numpy sound synthesis", "Web Audio API sound effects", "Claude write audio code", "prompt AI to make sound effects"]
faq:
  - q: "Can an LLM generate sound effects?"
    a: "A text-only LLM cannot output audio directly, but it can write synthesis code in Python or JavaScript that renders a WAV file when you run it."
  - q: "Which Python libraries do I need to synthesize sound?"
    a: "numpy for generating the waveform and scipy.io.wavfile for writing it to a WAV file are enough; pyloudnorm or ffmpeg can measure loudness afterwards."
  - q: "How do I make the LLM check its own audio if it can't listen?"
    a: "Ask it to measure what it can: exact sample count, integrated LUFS and true peak with ffmpeg ebur128, energy at each cue frame, and a spectrogram image."
  - q: "Should I use Python or the Web Audio API?"
    a: "Use Python when you want an offline WAV for a video edit, and use the Web Audio API when the sound must play live in a browser or web app."
  - q: "Why does my generated sound click at the start or end?"
    a: "Clicks usually come from a waveform that starts or stops at a non-zero value; ask for a short fade-in and fade-out of a few milliseconds."
---

# How to Prompt an LLM to Write Code That Generates Sound (Python and Web Audio)

To get an LLM to generate sound, ask it for synthesis code rather than audio: a Python script using numpy and scipy, or a Web Audio API function, that renders the sound when you run it. The prompt that works best is numeric, with an exact sample count, sample rate, cue frames, a loudness target and a list of checks the model must run because it cannot listen.

This approach gives you sounds that are precise and reproducible. The tradeoff is timbre: synthesized sound is clean and controllable but will not pass for a real orchestra or a human voice.

## Why ask for code instead of audio?

Most strong coding models, including [Claude Opus 5.5](https://platform.claude.com/docs/en/models/opus-5-5/overview) and OpenAI's [GPT-6 Astra](https://developers.openai.com/api/docs/models/gpt-6-astra), output text, not audio files. OpenAI's model page for GPT-6 Astra lists audio and video as unsupported modalities. Code is the bridge: the model writes it, and your machine renders the sound.

Code also gives you properties that audio models struggle with:

- **Exact length.** A 15-second bed at 48 kHz is exactly 720,000 samples, not "about 15 seconds".
- **Exact cue timing.** An impact can land on sample 72,000 (frame 45 at 30 fps).
- **Reproducibility.** A fixed random seed gives the same file every run.
- **Editability.** You can change one number (key, tempo, decay) and re-render.

**Audio synthesis** is the creation of sound from mathematical signals such as sine waves, noise and envelopes, rather than from recordings.

## What should the prompt include?

A reliable synth-code prompt has five parts.

1. **Output contract.** File type, sample rate, bit depth, channels and exact sample count.
2. **Constraints.** Which libraries are allowed (for example "numpy/scipy only, no samples, no downloads") and a fixed seed.
3. **Timing grid.** Frame rate, BPM, and cue frames tied to events in the video.
4. **Sound description.** Plain words about timbre, pitch and envelope. Describe styles, not artists.
5. **Self-checks.** What the model must measure and fix before it reports back.

An **envelope** is the shape of a sound's level over time, usually described as attack, decay, sustain and release (ADSR).

## What does a working Python prompt look like?

Here is a prompt for a short UI chime you can paste into a code-capable assistant. It follows the same template as the [Success chime](https://opussounds.directory/e/ui-success-chime) entry on Opus Sounds Directory.

```text
Make a 0.5 s UI success sound for video at 30 fps.
Output: one WAV, 48 kHz / 16-bit / stereo, exactly 24000 samples.
Python + numpy/scipy only. Synthesise everything (no samples, no downloads). Fixed random seed 42.
Sound: two-tone chime, first tone at 880 Hz (A5), second at 1318.5 Hz (E6) starting 60 ms later.
Each tone: 5 ms attack, exponential decay to -60 dB within 400 ms. Add a quiet octave partial at 20%.
No energy above 8 kHz. 5 ms fade-out at the very end so the file ends at exactly 0.
Master: true peak <= -1 dBTP.
Verify: print the sample count, measure true peak with ffmpeg ebur128, render a spectrogram PNG.
Fix and re-render until every check passes, then report the numbers.
```

And a longer one for a riser, matching the [8s tension riser](https://opussounds.directory/e/riser-tension-8s) entry:

```text
Make an 8 s riser for video at 30 fps.
Output: one WAV, 48 kHz / 16-bit / stereo, exactly 384000 samples.
Python + numpy/scipy only. Synthesise everything. Fixed random seed.
Sound: white noise through a band-pass filter whose centre sweeps from 200 Hz to 8 kHz
(exponential curve), plus a stack of three detuned sines gliding up one octave.
Level rises steadily to maximum energy at frame 210 (sample 336000), then hard cut to silence
with a 2 ms fade to avoid a click.
Master: -14 LUFS integrated, true peak <= -1 dBTP.
Verify length, loudness and peak with ffmpeg ebur128; confirm the RMS peak falls within one frame
of sample 336000; render a spectrogram. Fix until every check passes.
```

## How do I make the model check audio it can't hear?

Tell it what to measure, then tell it to loop until the numbers pass. Useful checks:

- **Length:** `len(audio) == 720000`.
- **Loudness and peak:** run ffmpeg's [ebur128 filter](https://ffmpeg.org/ffmpeg-filters.html#ebur128) with `peak=true`, or use the Python library [pyloudnorm](https://github.com/csteinmetz1/pyloudnorm).
- **Cue timing:** compute RMS energy per video frame and confirm the jump happens on the cue frame.
- **Pitch:** check that the strongest frequencies match the notes you asked for.
- **Spectrogram:** render an image so the model (or you) can spot harsh highs, clicks or empty bands.

**True peak** is the estimated maximum level of the continuous analog waveform between samples, measured in dBTP, which can be higher than the highest sample value.

If you work in an agentic coding tool, the model can run these checks itself in a loop. In a plain chat, run the script locally and paste the printed numbers back.

## What does the minimal Python code look like?

The core of almost every generated script is short. The [scipy.io.wavfile.write](https://docs.scipy.org/doc/scipy/reference/generated/scipy.io.wavfile.write.html) function does the file writing and [numpy](https://numpy.org/doc/stable/) does the math:

```python
import numpy as np
from scipy.io import wavfile

sr = 48000
n = 24000                      # exactly 0.5 s
t = np.arange(n) / sr
env = np.exp(-t * 12)          # fast exponential decay
env[:240] *= np.linspace(0, 1, 240)   # 5 ms attack
tone = np.sin(2 * np.pi * 880 * t) * env
tone[-240:] *= np.linspace(1, 0, 240) # 5 ms fade-out
peak = 10 ** (-1.5 / 20)       # leave headroom under -1 dBTP
tone = tone / np.max(np.abs(tone)) * peak
stereo = np.column_stack([tone, tone])
wavfile.write("chime.wav", sr, (stereo * 32767).astype(np.int16))
```

Normalizing the sample peak to -1.5 dBFS is a rough shortcut. True peak can sit above the sample peak, so measure it after rendering.

## When should I use the Web Audio API instead?

Use the [Web Audio API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API) when the sound has to play inside a web page or app, for example a button click that triggers a chime. The same prompt structure works: ask for oscillator types, frequencies, gain envelopes in milliseconds and a total duration.

Short interface sounds, such as a camera shutter for a capture button, make a good first test because you can hear right away whether an envelope clicks:

[Camera shutter](/e/ui-camera-shutter)

If you need a file from browser code, an [OfflineAudioContext](https://developer.mozilla.org/en-US/docs/Web/API/OfflineAudioContext) renders the graph to a buffer faster than real time. Libraries like [Tone.js](https://tonejs.github.io/) add instruments and scheduling on top.

## Where can I find prompts that already work?

Start from a working prompt and change the numbers rather than writing from scratch. Opus Sounds Directory lists sound prompts next to their Python code, spectrogram and measured loudness, which lets you compare a prompt's targets with what the render actually measured. For text-to-audio models instead of code, browse [Hugging Face text-to-audio models](https://huggingface.co/models?pipeline_tag=text-to-audio). For general prompt-writing advice, Anthropic's [prompt engineering overview](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/overview) is worth reading.
