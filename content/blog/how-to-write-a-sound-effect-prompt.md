---
title: "How to Write a Good Sound Effect Prompt (With UI and App Sound Examples)"
slug: "how-to-write-a-sound-effect-prompt"
description: "A template for writing sound effect prompts that work, with copyable UI, notification and transition examples and the basics of UI sound design."
date: "2026-10-06"
keywords: ["sound effect prompt", "how to write AI sound prompts", "UI sound design", "app notification sound", "text to sound effects prompt", "UI sound effects"]
faq:
  - q: "What makes a good sound effect prompt?"
    a: "A good sound effect prompt states the exact length, format and timing, describes the sound in concrete physical terms such as pitch, attack and decay, and lists checks the result must pass."
  - q: "How long should a UI sound be?"
    a: "Short. Microsoft's Windows UX guidelines recommend sounds under one second, and taps and confirmations are usually far shorter, often a few hundred milliseconds."
  - q: "What frequency range works for UI sounds?"
    a: "Microsoft's guidelines suggest mid to high frequencies of about 600 Hz to 2 kHz, which are clear on small speakers without being harsh."
  - q: "Should I name an artist or a song in a sound prompt?"
    a: "No. Describe the style and the sound's physical properties instead; it is more precise and avoids copying someone else's work."
  - q: "Can sound be the only signal for a notification?"
    a: "No. The BBC's accessibility guidelines say notifications must be both visible and audible, so pair every sound with a visual cue."
---

# How to Write a Good Sound Effect Prompt (With UI and App Sound Examples)

A good sound effect prompt gives the generator a contract: exact length, format and cue timing, a concrete description of pitch, attack, decay and texture, and the checks the result must pass. Vague prompts like "a nice click" produce random results; numeric prompts produce sounds you can reproduce and fit to a frame.

This works whether you prompt a text-to-sound model or ask an LLM to write synthesis code. The examples below lean on UI and app sounds because they are short, common and unforgiving.

## What should every sound effect prompt include?

Use five parts, in this order:

1. **What and where.** "A 0.4 s UI error sound for an app demo video at 30 fps."
2. **Output contract.** Sample rate, bit depth, channels and exact sample count (0.4 s at 48 kHz is 19,200 samples).
3. **Timing.** Where the transient lands (frame 0, or a specific cue frame) and how the tail ends.
4. **Sound description.** Pitch or frequency band, attack time, decay shape, texture, and what to avoid.
5. **Checks.** Length, peak, and a spectrogram, with a rule to fix and re-render until they pass.

A **transient** is the short, high-energy start of a sound, such as the click at the front of a tap.

An **earcon** is a short, abstract sound that stands for an event or state in an interface, such as a success chime or an error tap.

## What words describe a sound precisely?

Swap adjectives for measurable properties wherever you can:

- **"Snappy"** becomes "attack under 5 ms, decay to silence within 120 ms".
- **"Warm"** becomes "low-pass at 3 kHz, most energy between 200 Hz and 1 kHz".
- **"Bright"** becomes "partials up to 6 kHz, no energy above 10 kHz".
- **"Soft"** becomes "true peak at -6 dBTP, rounded 10 ms attack".
- **"Big"** becomes "sub layer at 50 Hz plus a 1.5 s decaying tail".

Describe styles, not artists. "Glassy two-note chime" is clearer to a model than a product or song name, and it keeps you away from imitating someone's work.

## What are the basics of UI and app sound design?

UI sounds have a narrow job: confirm an action without getting in the way. Microsoft's [Windows UX guidelines on sound](https://learn.microsoft.com/en-us/windows/win32/uxguide/vis-sound) recommend sounds that are mid to high frequency (600 Hz to 2 kHz), short (less than one second), soft or moderate in volume, meaningful, pleasant rather than alarming, non-verbal and non-repetitive. They also note that people turn sound off entirely when it gets annoying.

Accessibility matters too. The BBC's [inclusive notifications guideline](https://www.bbc.co.uk/accessibility/forproducts/guides/mobile/inclusive-notifications/) says notifications must be both visible and audible, so a sound should never be the only signal.

A few practical rules follow:

- **Frequent sounds should be quieter and simpler.** A tap you hear 200 times a day should be almost nothing.
- **Rare, important sounds can be longer and richer.**
- **Success rises, errors fall or clash.** An upward interval reads as positive, a low muted thud or a dissonant interval reads as a problem, without needing to be loud.
- **Keep a family.** Use one key and a shared timbre across all your app's sounds so they feel related.

## What does a good UI sound prompt look like?

Here is a soft error tap, matching the [Soft error tap](https://opussounds.directory/e/ui-error-soft) entry on Opus Sounds Directory:

```text
Make a 0.4 s UI error sound for an app demo video at 30 fps.
Output: one WAV, 48 kHz / 16-bit / stereo, exactly 19200 samples.
Python + numpy/scipy only. Synthesise everything (no samples, no downloads). Fixed random seed.
Sound: low muted thud (sine at 180 Hz, 3 ms attack, decay to -60 dB in 150 ms) layered with a short
minor-second interval (E5 + F5, 60 ms, 15% level) so it reads as "not quite" without sounding alarming.
Transient at frame 0. No energy above 6 kHz. 5 ms fade-out so the file ends at exactly 0.
Master: true peak <= -3 dBTP.
Verify: print the sample count, measure true peak with ffmpeg ebur128, render a spectrogram.
Fix and re-render until every check passes, then report the numbers.
```

And a success chime in the same family, like the [Success chime](https://opussounds.directory/e/ui-success-chime) entry:

```text
Make a 0.5 s UI success chime for an app demo video at 30 fps.
Output: one WAV, 48 kHz / 16-bit / stereo, exactly 24000 samples.
Python + numpy/scipy only. Synthesise everything. Fixed random seed.
Sound: two-tone rising chime, E5 then B5 starting 70 ms later (a perfect fifth up).
Sine plus a quiet 2nd partial at 15%. 4 ms attack, exponential decay, gone by 450 ms.
Transient at frame 0. No harsh highs: nothing above 8 kHz.
Master: true peak <= -3 dBTP.
Verify length and peak with ffmpeg ebur128; render a spectrogram; fix until checks pass.
```

Both share an E-based palette, so they sound like they belong to the same app.

## How do I write prompts for transitions and stings?

The same structure scales up. For a transition, name the cue frame and the sample it maps to:

```text
Make a 1 s swipe whoosh for a vertical video transition at 30 fps.
Output: one WAV, 48 kHz / 16-bit / stereo, exactly 48000 samples.
Python + numpy/scipy only. Synthesise everything. Fixed random seed.
Sound: pink noise through a band-pass sweeping 400 Hz -> 5 kHz, left-to-right pan across the sweep,
loudest at frame 12 (sample 19200) where the cut happens, then a fast 200 ms fall-off.
Master: true peak <= -1 dBTP. Verify length and peak with ffmpeg ebur128 and report.
```

For a logo sting or a riser, add the musical key and the frame where the energy peaks. Browse the drops, risers and logo stings in Opus Sounds Directory for more prompts in this format, each shown with the code that rendered it and its measured loudness.

## Does the same prompt work with text-to-audio models?

Partly. Text-to-sound tools such as [ElevenLabs' sound effects generator](https://elevenlabs.io/sound-effects) and open models on [Hugging Face](https://huggingface.co/models?pipeline_tag=text-to-audio) such as [Stable Audio Open 1.0](https://huggingface.co/stabilityai/stable-audio-open-1.0) respond to descriptive words, and many let you set a duration. They generally don't guarantee an exact sample count or a transient on a given frame, so you'll trim and align in your editor.

Keep the descriptive half of the prompt (pitch, texture, attack, what to avoid) and drop the code-only parts like library constraints and seeds, unless the tool exposes a seed setting.

If you need exact timing, ask a code-capable model such as [Claude Opus 5.5](https://www.anthropic.com/claude-opus-5-5) for synthesis code instead.

## How short is too short for loudness measurement?

Very short sounds are hard to measure as "integrated loudness". BS.1770 meters work in 400 ms blocks, so a 0.4 s tap gives you barely one block. For UI sounds, set a true-peak ceiling and judge level by ear against the rest of your app or video mix, rather than chasing a LUFS number.

## FAQ

### What makes a good sound effect prompt?

A good sound effect prompt states the exact length, format and timing, describes the sound in concrete physical terms such as pitch, attack and decay, and lists checks the result must pass.

### How long should a UI sound be?

Short. Microsoft's Windows UX guidelines recommend sounds under one second, and taps and confirmations are usually far shorter, often a few hundred milliseconds.

### What frequency range works for UI sounds?

Microsoft's guidelines suggest mid to high frequencies of about 600 Hz to 2 kHz, which are clear on small speakers without being harsh.

### Should I name an artist or a song in a sound prompt?

No. Describe the style and the sound's physical properties instead; it is more precise and avoids copying someone else's work.

### Can sound be the only signal for a notification?

No. The BBC's accessibility guidelines say notifications must be both visible and audible, so pair every sound with a visual cue.
