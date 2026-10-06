---
title: "How to Add Sound Effects and Music to AI-Generated Videos"
slug: "how-to-add-sound-and-music-to-ai-generated-videos"
description: "A step-by-step workflow for adding music beds, sound effects and transitions to AI-generated video, with copyable sound prompts and loudness targets."
date: "2026-10-06"
keywords: ["add music to AI generated video", "AI video sound effects", "AI video audio", "video to audio model", "royalty-free music for AI video", "sound prompts for video"]
faq:
  - q: "Do AI video generators make sound?"
    a: "Some do. Google's Veo 3.1 generates synchronized audio with the video, while many other generators output silent clips that need audio added in an editor."
  - q: "What is the easiest way to add music to an AI-generated video?"
    a: "Export the clip, import it into an editor such as CapCut or DaVinci Resolve with a licensed music bed, trim the bed to the clip length, add short fades, and check loudness before export."
  - q: "Can AI add sound effects to an existing video?"
    a: "Yes. Video-to-audio models such as MMAudio and HunyuanVideo-Foley on Hugging Face generate sound effects from the video frames plus an optional text description."
  - q: "How loud should the music be in a short video?"
    a: "A common target for the finished mix is about -14 LUFS integrated with a true peak at or below -1 dBTP, with music sitting well under any voiceover."
  - q: "Where can I find free sound effects for AI videos?"
    a: "Freesound, Pixabay, the YouTube Audio Library, and Opus Sounds Directory all offer free sounds, each with its own license terms that you should read before use."
---

# How to Add Sound Effects and Music to AI-Generated Videos

To add sound to an AI-generated video, export the clip, lay a music bed and a few timed sound effects under it in an editor, and mix to a loudness target such as -14 LUFS. You can source that audio from a royalty-free library, generate it with an audio model, or have an LLM write synthesis code that renders sounds to the exact length and frame you need.

Most AI video still needs this step. Even when a generator produces audio, you will often want to replace or layer it so the timing and level fit your edit.

## Do AI video generators already make sound?

Some do and many don't. Google DeepMind's [Veo 3.1](https://deepmind.google/models/veo/) generates synchronized audio (dialogue, ambience and sound effects) together with the picture, and you can steer it through the prompt as described in the [Gemini API Veo docs](https://ai.google.dev/gemini-api/docs/veo). Other generators return a silent clip, so audio becomes a separate job.

Even with native audio, you get one render with the sound baked in. If you want a specific brand sting, a riser that hits on frame 210, or a bed that is exactly 15 seconds long, you will usually add or replace audio in post.

## What are the main ways to get audio for an AI video?

There are four practical routes, and most editors mix them.

1. **Stock and royalty-free libraries.** [Freesound](https://freesound.org), [Pixabay sound effects](https://pixabay.com/sound-effects/) and [Pixabay music](https://pixabay.com/music/), the [YouTube Audio Library](https://www.youtube.com/audiolibrary), and subscription catalogs like [Splice](https://splice.com/sounds).
2. **Text-to-audio models.** On Hugging Face you can browse [text-to-audio models](https://huggingface.co/models?pipeline_tag=text-to-audio) such as [MusicGen](https://huggingface.co/facebook/musicgen-large) and [Stable Audio Open 1.0](https://huggingface.co/stabilityai/stable-audio-open-1.0), or try a hosted demo like the [MusicGen Space](https://huggingface.co/spaces/facebook/MusicGen).
3. **Video-to-audio models.** These look at the frames and generate matching sound. [MMAudio](https://huggingface.co/hkchengrex/MMAudio) and [HunyuanVideo-Foley](https://huggingface.co/tencent/HunyuanVideo-Foley) are two open options on Hugging Face.
4. **Code-generated sound.** You ask an LLM such as [Claude Opus 5.5](https://www.anthropic.com/claude-opus-5-5) to write Python (numpy/scipy) that synthesizes the sound, then run it. Because the code sets every sample, length and cue timing are exact.

A **music bed** is a background music track placed under picture and voice, usually cut to a fixed length like 6, 15, 30 or 60 seconds.

A **video-to-audio model** is a generative model that takes video frames (and often a text hint) and outputs a soundtrack synchronized to what happens on screen.

## How do I add music to an AI video step by step?

Here is a workflow that works in [CapCut](https://www.capcut.com), [DaVinci Resolve](https://www.blackmagicdesign.com/products/davinciresolve) or any timeline editor.

1. **Lock the picture first.** Export the final AI clip at its delivery frame rate (often 30 fps for social). Note the exact length in frames. If you upscale or interpolate frames with a tool such as [Topaz Labs' Astra](https://www.topazlabs.com/astra), do that before the audio pass, because frame interpolation can change the frame count your cues depend on.
2. **Mark the cues.** Write down the frames where something should happen: the opening hit, the product reveal, the logo, the call to action.
3. **Pick or make a bed of the right length.** A 15-second ad wants a 15-second bed with a real ending, not a fade halfway through a bar.
4. **Add sound effects on cue.** Whooshes on cuts, a riser into the reveal, a short sting on the logo.
5. **Balance and measure.** Keep music under voiceover, then measure the whole mix with a loudness meter or ffmpeg.
6. **Export and check on a phone.** Most short-form viewing happens on phone speakers, so listen there before you publish.

## How do I time sound effects to the video frames?

Convert frames to seconds and samples before you place anything. At 30 fps one frame lasts 1/30 s (about 33.3 ms), which is 1,600 samples at 48 kHz. At 120 BPM one beat lasts 0.5 s, which is exactly 15 frames at 30 fps.

If your cue is frame 150, the sound should land at 5.0 seconds, or sample 240,000 at 48 kHz. Writing those numbers into the prompt is what makes generated sound line up without nudging clips by hand.

## What does a good sound prompt for video look like?

A good sound prompt is numeric. It states the output format, the exact length in samples, the frame rate, the cue frames and the loudness target, then describes the sound in plain words. Here are two you can copy and paste into a code-capable LLM.

A 15-second chaos-to-calm bed for a TikTok ad (the same structure as the [Chaos clocks → calm pad](https://opussounds.directory/e/chaos-calm-01) entry on Opus Sounds Directory):

```text
Make a 15 s music bed for a TikTok ad at 30 fps.
Output: one WAV, 48 kHz / 16-bit / stereo, exactly 720000 samples.
Python + numpy/scipy only. Synthesise everything (no samples, no downloads). Fixed random seed.
Timing: 120 BPM (1 beat = 15 frames). Cues: frame 0 = hit; frame 150 = chaos stops, calm begins;
last beat = soft ending that fades to exactly 0.
Sound: chaos (clashing clocks, notification pings, glitchy drums, rising noise) ->
calm (warm maj9 pad, felt piano, soft half-time pulse), key D major.
Master: -14 LUFS integrated, true peak <= -1 dBTP.
You can't listen, so verify: measure loudness and peak with ffmpeg ebur128, check the exact length,
confirm the energy change lands on each cue frame, render a spectrogram. Fix and re-render until
every check passes, then report the numbers.
```

A 2-second whoosh into a hit for a hard cut (compare with the [Whoosh into hit](https://opussounds.directory/e/drop-whoosh-stinger) entry):

```text
Make a 2 s whoosh stinger for video at 30 fps.
Output: one WAV, 48 kHz / 16-bit / stereo, exactly 96000 samples.
Python + numpy/scipy only. Synthesise everything. Fixed random seed.
Sound: band-pass noise sweep rising from 300 Hz to 6 kHz, landing in a short metallic hit at frame 30
(sample 48000), then a 0.5 s decaying tail. No click at the start or end.
Master: true peak <= -1 dBTP. Verify length and peak with ffmpeg ebur128 and report the numbers.
```

## How loud should music and sound effects be?

A common target for a finished social or YouTube mix is about -14 LUFS integrated with a true peak no higher than -1 dBTP. Platforms adjust playback differently and not all publish a fixed number, so treat -14 as a sensible reference, not a rule.

**LUFS** (Loudness Units relative to Full Scale) is a measure of perceived loudness defined in [ITU-R BS.1770](https://www.itu.int/rec/R-REC-BS.1770) and used by the [EBU R128](https://tech.ebu.ch/publications/r128) recommendation.

You can measure a file with ffmpeg's [ebur128 filter](https://ffmpeg.org/ffmpeg-filters.html#ebur128):

```bash
ffmpeg -i final_mix.wav -af ebur128=peak=true -f null -
```

## Which licenses should I check before publishing?

Read the license for every sound, even free ones. Freesound sounds carry Creative Commons licenses (CC0, Attribution, or Attribution-NonCommercial), as its [FAQ](https://freesound.org/help/faq/) explains. Pixabay's [license summary](https://pixabay.com/service/license-summary/) allows free use without attribution but bans reselling the files as-is. Audio Library tracks are cleared for YouTube, and some require credit in the description. Model weights differ too: MusicGen's weights are released under CC-BY-NC 4.0, so check a model card before you use its output commercially.

For sounds you render yourself from code, you control the inputs, which keeps licensing simple. Opus Sounds Directory publishes the prompt, the Python code and a spectrogram for each entry so you can re-render or change a sound. Most of its current entries are local numpy synthesis written to Opus-style prompts, and each entry page says how it was made.

## FAQ

### Do AI video generators make sound?

Some do. Google's Veo 3.1 generates synchronized audio with the video, while many other generators output silent clips that need audio added in an editor.

### What is the easiest way to add music to an AI-generated video?

Export the clip, import it into an editor such as CapCut or DaVinci Resolve with a licensed music bed, trim the bed to the clip length, add short fades, and check loudness before export.

### Can AI add sound effects to an existing video?

Yes. Video-to-audio models such as MMAudio and HunyuanVideo-Foley on Hugging Face generate sound effects from the video frames plus an optional text description.

### How loud should the music be in a short video?

A common target for the finished mix is about -14 LUFS integrated with a true peak at or below -1 dBTP, with music sitting well under any voiceover.

### Where can I find free sound effects for AI videos?

Freesound, Pixabay, the YouTube Audio Library, and Opus Sounds Directory all offer free sounds, each with its own license terms that you should read before use.
