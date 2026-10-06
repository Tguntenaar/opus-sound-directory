---
title: "Whoosh, Riser and Transition Sound Effects: How to Use Them in Video Editing"
slug: "whoosh-and-transition-sound-effects-for-video-editing"
description: "How to place whooshes, risers and impacts on cuts so transitions feel smooth, with frame timing tips, free sources and copyable prompts."
date: "2026-10-06"
keywords: ["transition sound effects", "whoosh sound effect", "riser sound effect", "swoosh sound effect for video", "impact sound effect", "sound effects for video transitions"]
faq:
  - q: "What is a whoosh sound effect used for?"
    a: "A whoosh sells movement across a cut, such as a swipe, zoom, whip pan or text flying in, by sweeping noise past the listener as the picture changes."
  - q: "Where should a whoosh start relative to the cut?"
    a: "Start it a few frames before the cut so its loudest point lands on the first frame of the new shot, then let the tail fade just after."
  - q: "What is a riser in video editing?"
    a: "A riser is a sound that builds in pitch, brightness or volume over a few seconds to create tension, usually cutting off or resolving into an impact at a reveal."
  - q: "Where can I get free transition sound effects?"
    a: "Pixabay sound effects and Freesound both have large whoosh and riser collections; check each sound's license, and you can also synthesize your own with code."
  - q: "How many transition sounds should I use?"
    a: "Fewer than you think. Put sound on the cuts that carry meaning, such as reveals and section changes, and leave routine cuts quiet."
---

# Whoosh, Riser and Transition Sound Effects: How to Use Them in Video Editing

Transition sound effects work when their loudest moment lands on the cut: start a whoosh a few frames early so it peaks on the first frame of the new shot, run a riser for one to a few seconds into a reveal, and drop an impact exactly on the reveal frame. Use them on the cuts that matter, not on every cut.

Here's how each one works, where to get them, and how to make your own that fit to the frame.

## What are the main types of transition sound effects?

Most edits use four kinds:

- **Whoosh (or swoosh).** A short sweep of noise that sells motion across a cut.
- **Riser.** A build of pitch, brightness or volume that creates tension before a reveal.
- **Impact (or hit).** A short, heavy transient that marks the reveal or a hard cut.
- **Reverse swell.** A sound played backwards so it swells into the cut instead of decaying away from it.

A **whoosh** is a short sound effect, usually filtered noise with a rising and falling level, that suggests something moving quickly past the listener.

A **riser** is a sound that increases in pitch, brightness or volume over time to build anticipation, typically ending at a cut, drop or reveal.

## How do I time a whoosh to a cut?

Find the loudest point of the whoosh (look at the waveform), then slide the clip so that peak sits on the first frame of the incoming shot. In practice the whoosh starts a few frames before the cut.

At 30 fps, one frame is about 33 ms. A 0.6-second whoosh that peaks halfway through starts 9 frames before the cut. If the movement on screen goes left to right, pan the whoosh the same way.

Real-world movement past a listener also drops in pitch as it passes. That's the [Doppler effect](https://en.wikipedia.org/wiki/Doppler_effect), and a slight downward pitch bend after the peak makes a whoosh feel physical.

## How do I use a riser into a reveal?

Decide where the reveal frame is, then work backwards. A riser that builds for 2 to 8 seconds should hit its maximum energy on, or one frame before, the reveal, then either cut to silence or hand off to an impact.

Two tips that help:

- **Cut, don't fade.** An abrupt stop right before the reveal makes the new shot feel bigger.
- **Leave room for voice.** If someone speaks over the build, keep the riser below the voice and filter out some of its midrange.

The [Shepard tone](https://en.wikipedia.org/wiki/Shepard_tone) is a related auditory illusion: octave-spaced sine waves that seem to rise forever. It's a handy reference when you want a build that feels endless.

## How do J-cuts and L-cuts fit with transition sounds?

A **J-cut** is an edit where the audio of the next shot starts before its picture appears. An **L-cut** is the reverse: the audio of the previous shot continues after the picture has changed. Both are explained in Wikipedia's [J cut](https://en.wikipedia.org/wiki/J_cut) and [L cut](https://en.wikipedia.org/wiki/L_cut) articles.

These overlaps smooth transitions without any extra effect. Often, a J-cut plus a quiet whoosh does more than a loud whoosh alone.

## Where can I find free whoosh and riser sounds?

Good starting points:

- [Pixabay whoosh sound effects](https://pixabay.com/sound-effects/search/whoosh/), covered by Pixabay's [license summary](https://pixabay.com/service/license-summary/).
- [Freesound whoosh search](https://freesound.org/search/?q=whoosh), where each sound has its own Creative Commons license, explained in the [Freesound FAQ](https://freesound.org/help/faq/).
- The [YouTube Audio Library](https://www.youtube.com/audiolibrary) sound effects tab, for YouTube videos.
- Synthesized sounds from your own code, or from Opus Sounds Directory, which publishes the prompt and Python code behind each riser, drop and transition.

## How do I make a whoosh that fits my cut exactly?

Generate it to the frame. These prompts work with any code-capable LLM. Each one matches an entry you can play here:

[Whoosh into hit](/e/drop-whoosh-stinger)

```text
Make a 0.8 s whoosh for a left-to-right swipe transition at 30 fps.
Output: one WAV, 48 kHz / 16-bit / stereo, exactly 38400 samples.
Python + numpy/scipy only. Synthesise everything (no samples, no downloads). Fixed random seed.
Sound: pink noise through a band-pass filter sweeping 400 Hz -> 5 kHz -> 1.5 kHz,
loudest at frame 15 (sample 24000, where the cut is), pan from -0.8 to +0.8 across the sweep,
slight 5% pitch drop after the peak (Doppler feel). 3 ms fade in/out, no clicks.
Master: true peak <= -1 dBTP.
Verify length and peak with ffmpeg ebur128; confirm the RMS maximum is in frame 15; render a spectrogram.
```

And a riser that cuts on a reveal:

[8s tension riser](/e/riser-tension-8s)

```text
Make an 8 s riser into a reveal at 30 fps.
Output: one WAV, 48 kHz / 16-bit / stereo, exactly 384000 samples.
Python + numpy/scipy only. Synthesise everything. Fixed random seed.
Sound: white noise through a band-pass whose centre sweeps 200 Hz -> 8 kHz on an exponential curve,
plus three detuned sines gliding up one octave. Energy rises steadily to a maximum at frame 210
(sample 336000), then a hard cut with a 2 ms fade to silence for the rest of the file.
Master: -14 LUFS integrated, true peak <= -1 dBTP.
Verify length, loudness and peak with ffmpeg ebur128; confirm the cut lands within one frame of 210.
```

To finish the move, add an impact on the reveal frame:

[Heavy impact drop](/e/drop-impact-heavy)

```text
Make a 3 s impact for a reveal at 30 fps.
Output: one WAV, 48 kHz / 16-bit / stereo, exactly 144000 samples.
Python + numpy/scipy only. Synthesise everything. Fixed random seed.
Sound: sub drop 120 Hz -> 40 Hz, short noise burst, 1.2 s tail; peak impact at frame 45 (sample 72000).
Master: true peak <= -1 dBTP. Verify with ffmpeg ebur128 and report the numbers.
```

## How loud should transition sounds be?

Quieter than you think. Transition sounds should support the picture and never cover dialogue. Set them by ear against the voice, then measure the full mix. A common online target is about -14 LUFS integrated with true peak at or below -1 dBTP, measured with ffmpeg's [ebur128 filter](https://ffmpeg.org/ffmpeg-filters.html#ebur128).

If you stack a riser, whoosh and impact on one moment, check the true peak there in particular. Stacked transients are where clipping usually shows up.

## FAQ

### What is a whoosh sound effect used for?

A whoosh sells movement across a cut, such as a swipe, zoom, whip pan or text flying in, by sweeping noise past the listener as the picture changes.

### Where should a whoosh start relative to the cut?

Start it a few frames before the cut so its loudest point lands on the first frame of the new shot, then let the tail fade just after.

### What is a riser in video editing?

A riser is a sound that builds in pitch, brightness or volume over a few seconds to create tension, usually cutting off or resolving into an impact at a reveal.

### Where can I get free transition sound effects?

Pixabay sound effects and Freesound both have large whoosh and riser collections; check each sound's license, and you can also synthesize your own with code.

### How many transition sounds should I use?

Fewer than you think. Put sound on the cuts that carry meaning, such as reveals and section changes, and leave routine cuts quiet.
