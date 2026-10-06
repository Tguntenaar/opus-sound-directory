---
title: "How to Make an Audio Logo (Sonic Logo) for Your Videos and App"
slug: "how-to-make-an-audio-logo"
description: "How to make an audio logo or sonic logo: length, notes, timbre, versions for video and app, and copyable prompts to generate a logo sting with code."
date: "2026-10-06"
keywords: ["how to make an audio logo", "sonic logo", "audio logo", "logo sting sound", "sound logo for video intro", "sonic branding"]
faq:
  - q: "What is an audio logo?"
    a: "An audio logo, or sonic logo, is a short, repeatable sound that identifies a brand the way a visual logo does, usually played at the start or end of a video or when an app opens."
  - q: "How long should an audio logo be?"
    a: "Short. Most audio logos run about one to three seconds, which is long enough to remember and short enough for intros, end cards and app launches."
  - q: "Can I trademark an audio logo?"
    a: "Sound marks can be registered as trademarks in some jurisdictions, including the United States; check with your national trademark office or a lawyer."
  - q: "What is the difference between a logo sting and an audio logo?"
    a: "A logo sting is the sound played under a logo animation in a video; an audio logo is the brand's core sound, which a sting often contains along with extra texture."
  - q: "Can I make an audio logo with AI?"
    a: "Yes. You can prompt a text-to-music model for short variations or have an LLM write synthesis code, then pick, refine and test a version by ear."
---

# How to Make an Audio Logo (Sonic Logo) for Your Videos and App

To make an audio logo, write a short brief (three brand adjectives and where it will play), sketch a two-to-five-note motif one to three seconds long, choose one main timbre that reads on a phone speaker, and make a full, short and quiet version. Then test it in context, at the end of a real video and on app open, before you commit.

You don't need an orchestra. A clear motif and a consistent sound do most of the work.

## What is an audio logo?

An **audio logo** (also called a sonic logo or sound logo) is a short, repeatable sound that identifies a brand, the way a visual logo does. Wikipedia covers the legal side under [sound trademark](https://en.wikipedia.org/wiki/Sound_trademark) and the broader practice under [sonic branding](https://en.wikipedia.org/wiki/Sonic_branding).

A **logo sting** is the sound under a logo animation in a video. It usually contains the audio logo plus extra texture such as a whoosh in or a shimmer tail.

**Sonic branding** is the consistent use of sound (logos, UI sounds, music) to make a brand recognizable by ear.

## How long should an audio logo be?

Keep it to about one to three seconds. That's long enough for a short melodic shape and short enough to sit on an end card, a video intro or an app launch without slowing anything down.

For video, think in frames. At 30 fps, 2.5 seconds is 75 frames. Decide which frame the logo appears on and which frame the "sparkle" or final note lands on, then build the sound around those.

## What makes an audio logo memorable?

A few principles show up again and again:

- **Few notes.** Two to five notes with one clear shape (a rise, a fall, or one leap) are easy to recall.
- **One main timbre.** Pick one main sound, such as a bell, marimba, pluck or soft piano, and keep it.
- **Midrange focus.** Phone and laptop speakers reproduce little deep bass, so put the identity in the mids.
- **A clear ending.** Either resolve (it feels finished) or end on a deliberately open note (it feels like "more is coming").
- **Survives repetition.** People may hear it many times a day in an app. If it grates on the tenth listen, simplify.

## Which versions do I need?

Make the audio logo as a small set, not a single file:

1. **Full sting (2 to 3 s)** for video intros and end cards.
2. **Short version (about 1 s)** for bumpers and tight cuts.
3. **Quiet UI version (under 0.5 s)** for app open or success states.
4. **Stems** (motif, texture, tail) so editors can adapt it.

Write down the key, tempo and main timbre, so anyone extending it later stays consistent.

## How do I make a logo sting with code?

Code is a good fit because the result is identical every render and lands on a frame. This prompt matches an entry you can play on Opus Sounds Directory:

[Bright logo sting](/e/logo-sting-bright)

```text
Make a 2.5 s logo sting for a video end card at 30 fps.
Output: one WAV, 48 kHz / 16-bit / stereo, exactly 120000 samples.
Python + numpy/scipy only. Synthesise everything (no samples, no downloads). Fixed random seed.
Motif: three rising notes C5, E5, G5 at frames 0, 6 and 12 (samples 0, 9600, 19200),
bell-like timbre (sine + inharmonic partials at 2.76x and 5.4x, 3 ms attack, 1.2 s decay),
then a soft Cmaj7 chord bloom from frame 18 and a shimmer sparkle at frame 60 (sample 96000).
Energy mostly between 400 Hz and 4 kHz. Tail decays to exactly 0 by the last sample.
Master: true peak <= -1 dBTP; leave headroom for a voiceover.
Verify length and peak with ffmpeg ebur128; render a spectrogram; fix until checks pass.
```

Then make the short, quiet UI version from the same motif. This one is in the same family as this entry:

[Success chime](/e/ui-success-chime)

The success chime was the directory's first sound generated by Claude Opus 5.5. Every entry is now Opus 5.5 output, with the model writing the Python code that renders it.

```text
Make a 0.5 s app-open version of the audio logo above.
Output: one WAV, 48 kHz / 16-bit / stereo, exactly 24000 samples.
Python + numpy/scipy only. Synthesise everything. Fixed random seed.
Motif: the same rising C5 -> G5 interval only (skip E5), same bell timbre, G5 starting 70 ms after C5.
4 ms attack, exponential decay gone by 450 ms, nothing above 8 kHz, ends at exactly 0.
Master: true peak <= -3 dBTP (quieter than the full sting).
Verify length and peak with ffmpeg ebur128 and report the numbers.
```

For the 6-second bumper version with a groove behind the motif, compare this entry:

[6s bumper sting](/e/ad-bed-6-bumper)

Each entry shows the prompt, the Python code Opus 5.5 wrote, a spectrogram and measured loudness.

Two more stings show how far one idea stretches, from a plucked kalimba-style motif to a dark cinematic reveal:

[Organic kalimba logo](/e/logo-sting-organic)

[Dark cinematic logo reveal](/e/logo-sting-dark-cinematic)

## Can I use AI music tools for an audio logo?

Yes, as a sketchpad. Text-to-music models such as [MusicGen](https://huggingface.co/facebook/musicgen-large) or [Stable Audio Open 1.0](https://huggingface.co/stabilityai/stable-audio-open-1.0) on Hugging Face, or [ElevenLabs Music](https://elevenlabs.io/music), can produce many short ideas fast. Say "instrumental", give the length, and describe the note count and shape in words.

Check licenses carefully for brand use. MusicGen's weights are CC-BY-NC 4.0 (non-commercial), and Stable Audio Open uses the Stability AI Community License. For a brand asset you plan to use for years, simple synthesized code or a commissioned composer gives you the clearest ownership.

## Can I protect my audio logo?

Sound marks can be registered as trademarks in some places, including the United States. The USPTO's [trademark basics](https://www.uspto.gov/trademarks/basics/what-trademark) explain what a trademark is, and its page on [trademark, patent or copyright](https://www.uspto.gov/trademarks/basics/trademark-patent-copyright) explains which protection covers what. For anything you rely on commercially, talk to a trademark lawyer.

Also make sure your motif isn't a copy of an existing one. Play it to a few people and ask what it reminds them of.
