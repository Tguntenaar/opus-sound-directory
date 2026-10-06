---
title: "Open-Source AI Audio Models on Hugging Face: Music, Sound Effects and Video-to-Audio"
slug: "open-source-ai-audio-models-on-hugging-face"
description: "A guide to open AI audio models on Hugging Face (MusicGen, AudioGen, Stable Audio Open, AudioLDM 2, ACE-Step, MMAudio) with what each does and its license."
date: "2026-10-06"
keywords: ["open source text to audio model", "Hugging Face audio models", "open source AI music generator", "MusicGen", "Stable Audio Open", "AI sound effects generator open source"]
faq:
  - q: "What is the best open-source AI music model?"
    a: "It depends on your use. MusicGen and Stable Audio Open are widely used for short clips, and ACE-Step 1.5 targets full songs under an MIT license; test a few against your own prompts."
  - q: "Can I use music from MusicGen commercially?"
    a: "Be careful. Meta releases the MusicGen weights under CC-BY-NC 4.0, a non-commercial license, so check the model card and get legal advice before commercial use."
  - q: "Which open model makes sound effects rather than music?"
    a: "AudioGen is trained for text-to-sound effects, AudioLDM 2 covers general sound effects and music, and Stable Audio Open generates both short sounds and music."
  - q: "Is there an open model that adds sound to a video?"
    a: "Yes. MMAudio and HunyuanVideo-Foley are video-to-audio models on Hugging Face that generate sound effects synchronized to video frames."
  - q: "Do I need a GPU to run these models?"
    a: "For reasonable speed, usually yes, but many models have hosted demos in Hugging Face Spaces that you can try in a browser first."
---

# Open-Source AI Audio Models on Hugging Face: Music, Sound Effects and Video-to-Audio

The main open AI audio models on Hugging Face are MusicGen and ACE-Step for music, AudioGen and AudioLDM 2 for sound effects, Stable Audio Open for short music and sounds, and MMAudio and HunyuanVideo-Foley for adding sound to video. Their licenses differ a lot, and several are non-commercial, so read the model card before using output in client work.

Here is what each one does, how long a clip it makes, and what its license says.

## What is a text-to-audio model?

A **text-to-audio model** is a generative model that takes a written description, such as "rain on a tin roof" or "upbeat synth pop, 120 BPM", and outputs an audio waveform.

A **video-to-audio model** takes video frames (often plus a text hint) and generates sound that is synchronized to what happens on screen.

You can browse both on Hugging Face's [text-to-audio model list](https://huggingface.co/models?pipeline_tag=text-to-audio).

## Which open models generate music?

**MusicGen (Meta, AudioCraft).** A text-to-music model available in several sizes, including [musicgen-small](https://huggingface.co/facebook/musicgen-small), [musicgen-large](https://huggingface.co/facebook/musicgen-large) and a melody-conditioned version. It runs in the Transformers library ([MusicGen docs](https://huggingface.co/docs/transformers/model_doc/musicgen)) and in Meta's [AudioCraft](https://github.com/facebookresearch/audiocraft) repo. AudioCraft's code is MIT, but the model weights are CC-BY-NC 4.0 (non-commercial). Try it in the [MusicGen Space](https://huggingface.co/spaces/facebook/MusicGen).

**Stable Audio Open (Stability AI).** [Stable Audio Open 1.0](https://huggingface.co/stabilityai/stable-audio-open-1.0) generates variable-length stereo audio up to 47 seconds at 44.1 kHz, and [Stable Audio Open Small](https://huggingface.co/stabilityai/stable-audio-open-small) goes up to 11 seconds. Both use the Stability AI Community License, and you accept terms on the model page to download. It runs with [stable-audio-tools](https://github.com/Stability-AI/stable-audio-tools) or the [Diffusers Stable Audio pipeline](https://huggingface.co/docs/diffusers/api/pipelines/stable_audio).

**ACE-Step.** [ACE-Step 1.5](https://huggingface.co/ACE-Step/Ace-Step1.5) is a music generation model released under the MIT license. Its model card says generated music can be used commercially and that it scales from short loops to long compositions. The earlier [ACE-Step v1 3.5B](https://huggingface.co/ACE-Step/ACE-Step-v1-3.5B) is Apache-2.0.

## Which open models generate sound effects?

**AudioGen (Meta).** [audiogen-medium](https://huggingface.co/facebook/audiogen-medium) is trained for text-to-sound effects, with generation length set in code (the card's example uses 5 seconds). Weights are CC-BY-NC 4.0.

**AudioLDM 2.** [AudioLDM 2](https://huggingface.co/cvssp/audioldm2) is a latent diffusion model for text-conditional sound effects, speech and music, available through the [Diffusers AudioLDM 2 pipeline](https://huggingface.co/docs/diffusers/api/pipelines/audioldm2). License: CC-BY-NC-SA 4.0.

**Bark (Suno).** [Bark](https://huggingface.co/suno/bark) is mainly a text-to-speech model, but its card says it can also produce music, background noise, simple sound effects and nonverbal sounds like laughing. License: MIT.

## Which open models add sound to video?

**MMAudio.** [MMAudio](https://huggingface.co/hkchengrex/MMAudio) generates audio from video (and text). The [code](https://github.com/hkchengrex/MMAudio) is MIT, and the checkpoints are CC-BY-NC 4.0 for non-commercial use.

**HunyuanVideo-Foley (Tencent).** [HunyuanVideo-Foley](https://huggingface.co/tencent/HunyuanVideo-Foley) generates 48 kHz sound effects synchronized to video, guided by a text description. It uses the Tencent Hunyuan community license.

## How do the licenses compare?

| Model | Main use | License on the model card |
|---|---|---|
| MusicGen | Music | CC-BY-NC 4.0 (weights) |
| AudioGen | Sound effects | CC-BY-NC 4.0 |
| Stable Audio Open 1.0 / Small | Music and sounds, up to 47 s / 11 s | Stability AI Community License |
| AudioLDM 2 | Sound effects, music, speech | CC-BY-NC-SA 4.0 |
| ACE-Step 1.5 | Music | MIT |
| Bark | Speech, some sounds | MIT |
| MMAudio | Video-to-audio | CC-BY-NC 4.0 (checkpoints) |
| HunyuanVideo-Foley | Video-to-audio | Tencent Hunyuan community license |

**CC-BY-NC** is a Creative Commons license that allows reuse with credit but forbids commercial use. Licenses and model versions change, so treat this table as a starting point and read each card yourself.

## When should I use code synthesis instead of a model?

Generative models are good at texture and realism. They are weaker at exact length, frame-accurate hits and identical re-renders. When you need a whoosh on frame 30 or a bed that is exactly 720,000 samples, it's often easier to have an LLM write synthesis code.

Opus Sounds Directory collects prompts in that style next to the Python code, spectrogram and measured loudness. Most entries are local numpy synthesis written to Opus-style prompts, and each page says how it was made. Here are two examples and their prompts.

[Notification storm → breath](/e/chaos-calm-03)

```text
Make a 10 s music bed for a vertical video ad at 30 fps.
Output: one WAV, 48 kHz / 16-bit / stereo, exactly 480000 samples.
Python + numpy/scipy only. Synthesise everything (no samples, no downloads). Fixed random seed.
Timing: 100 BPM (1 beat = 18 frames). Cues: frame 0 = alert stack; frame 120 = notifications mute;
last beat = soft ending that fades to exactly 0.
Sound: chaos (stacked notification pings, rapid clicks, tense pulse) -> calm (airy pad,
slow exhale noise bed, single soft bell), key F major.
Master: -14 LUFS integrated, true peak <= -1 dBTP.
Verify length, loudness and peak with ffmpeg ebur128; confirm the energy drop at frame 120.
```

[Soft error tap](/e/ui-error-soft)

```text
Make a 0.4 s UI error sound at 30 fps.
Output: one WAV, 48 kHz / 16-bit / stereo, exactly 19200 samples.
Python + numpy/scipy only. Synthesise everything. Fixed random seed.
Sound: low muted thud (sine at 180 Hz, 3 ms attack, 150 ms decay) plus a quiet minor-second interval
(E5 + F5, 60 ms). Transient at frame 0, nothing above 6 kHz, 5 ms fade-out to exactly 0.
Master: true peak <= -3 dBTP. Verify length and peak with ffmpeg ebur128 and report the numbers.
```

A good hybrid workflow: generate texture with a model (rain, crowd, a music idea), then use code for the timed parts (hits, risers, stings) and mix both.

## How do I write prompts for these models?

Describe the sound plainly and add the facts the model can use:

- **Genre or sound source** ("lo-fi hip hop", "heavy wooden door").
- **Tempo and key** for music, if the model responds to them.
- **Instrumentation or texture** ("muted piano, vinyl crackle").
- **Duration**, set in the code or UI rather than the text where possible.
- **What to avoid** ("no vocals", "no reverb tail").

Then generate several takes and pick by ear. These models aren't deterministic unless you fix the seed.

## FAQ

### What is the best open-source AI music model?

It depends on your use. MusicGen and Stable Audio Open are widely used for short clips, and ACE-Step 1.5 targets full songs under an MIT license; test a few against your own prompts.

### Can I use music from MusicGen commercially?

Be careful. Meta releases the MusicGen weights under CC-BY-NC 4.0, a non-commercial license, so check the model card and get legal advice before commercial use.

### Which open model makes sound effects rather than music?

AudioGen is trained for text-to-sound effects, AudioLDM 2 covers general sound effects and music, and Stable Audio Open generates both short sounds and music.

### Is there an open model that adds sound to a video?

Yes. MMAudio and HunyuanVideo-Foley are video-to-audio models on Hugging Face that generate sound effects synchronized to video frames.

### Do I need a GPU to run these models?

For reasonable speed, usually yes, but many models have hosted demos in Hugging Face Spaces that you can try in a browser first.
