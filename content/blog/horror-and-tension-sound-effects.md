---
title: "Horror and Tension Sound Effects: Heartbeats, Braams and Silence"
slug: "horror-and-tension-sound-effects"
description: "How accelerating heartbeats, risers, braams and sudden silence build and pay off tension, with frame-timed prompts."
date: "2026-10-06"
keywords: ["horror sound effects", "tension sound effects", "heartbeat sound effect", "braam sound effect", "jump scare sound", "suspense sound effects for video"]
faq:
  - q: "What sounds create tension in a video?"
    a: "Sounds that build steadily without resolving: a heartbeat that speeds up, a rising tone or riser, low rumbles, high thin rings, and breathing that gets faster."
  - q: "What is a braam sound?"
    a: "A braam is a loud, low, brass-like blast popular in 2010s action and thriller trailers, often linked with the film Inception."
  - q: "Why does silence work in horror?"
    a: "Cutting all sound after a long build leaves the viewer braced for a hit that hasn't come yet, so the next sound, or the lack of one, lands harder."
  - q: "Where can I find free heartbeat and horror sound effects?"
    a: "Pixabay and Freesound both have heartbeat and horror searches with stated licenses, and the BBC Sound Effects archive allows personal and educational use."
  - q: "How do I keep horror sound effects from clipping?"
    a: "Leave headroom for the big hit, keep sub energy in mono, limit to a true peak around -1 dBTP, and measure the final mix with a loudness meter."
---

# Horror and Tension Sound Effects: Heartbeats, Braams and Silence

Tension sound effects work by building without resolving: a heartbeat that speeds up, a rising tone, faster breathing, a thin high ring. Horror then pays that build off in one of two ways: a loud hit such as a braam, or a sudden cut to silence that leaves the audience braced.

Both are easy to plan to the frame, which matters because a scare that lands one beat late feels flat.

## What makes a sound feel tense?

Tension comes from expectation. A few reliable ingredients:

- **Acceleration.** Anything that speeds up (a heartbeat, a pulse, footsteps) suggests something is coming.
- **Rising pitch.** A rising tone, or **riser**, signals approach.
- **Low rumble.** Sub-bass you feel more than hear adds unease.
- **Thin, high rings.** A faint tone like tinnitus suggests shock or stress.
- **Breath.** Faster, shallower breathing tells the audience a character is scared.

A **Shepard tone** is an auditory illusion of a pitch that seems to rise forever ([Wikipedia](https://en.wikipedia.org/wiki/Shepard_tone)), used in film scores for endless tension.

## How do you make a heartbeat sound effect?

A heartbeat is two low thumps close together, "lub-dub", repeating. The "lub" is a bit longer and lower; the "dub" is shorter and slightly higher. Make it speed up over the shot and the build does most of the work for you.

Here's an accelerating heartbeat that runs from 60 to about 150 BPM, then flatlines mid-beat:

[Accelerating heartbeat](/e/heartbeat-tension-12s)

```text
Write Python (numpy/scipy only, no samples) that renders a 12-second accelerating heartbeat.
Output: one WAV, 48 kHz / 16-bit / stereo, exactly 576000 samples. Fixed random seed.
Sound: "lub-dub" pairs of mono sub thumps (a pitch-dropping sine plus a muffled knock; the dub is
shorter and slightly higher), starting on frame 0 (30 fps) at 60 BPM and speeding up smoothly to
about 150 BPM, each beat harder than the last. Above it, a faint high tinnitus ring fades in and
beats slowly between the ears. Under it, breath-like noise moves from slow deep breaths to panting.
On frame 330 (11.0 s), in the middle of a beat, cut everything to silence. Then one distant,
muffled heartbeat thud before the end.
Master: true peak <= -1 dBTP, sub energy in mono.
Verify with ffmpeg ebur128: exact length, true peak, and that the level after 11.0 s is near silence
apart from the one thud. Report the numbers.
```

For a ready-made option, search [Pixabay heartbeat sound effects](https://pixabay.com/sound-effects/search/heartbeat/) or [Freesound heartbeat recordings](https://freesound.org/search/?q=heartbeat), checking each sound's license.

## What is a braam?

A **braam** is a loud, low, brass-like blast used as a dramatic hit. Wikipedia's [Braaam](https://en.wikipedia.org/wiki/Braaam) article describes it as a sound popular in 2010s action film trailers and associated with Inception, though its exact origin is disputed.

A braam works best after a short gap. A reverse cymbal or riser that stops just before the hit creates a tiny vacuum, and the low blast then fills it.

This dark logo reveal uses that structure: metallic scrapes, a reverse cymbal that stops 45 ms early, then a braam on frame 75 (2.5 s):

[Dark cinematic logo reveal](/e/logo-sting-dark-cinematic)

```text
Write Python (numpy/scipy only) that renders a 4-second dark cinematic reveal centred on low D.
Output: one WAV, 48 kHz / 16-bit / stereo, exactly 192000 samples. Fixed random seed.
Sound: on frame 0 (30 fps) a dull knock opens a mono D1 sub rumble that slowly swells. Above it a
metallic scrape (friction exciting an inharmonic resonator bank) slides across the stereo field,
and a harder second scrape takes over at 1.0 s. From 1.05 s a reverse cymbal rises and stops
sharply 45 ms before the hit. On frame 75 (2.5 s) a braam lands: a D minor stack of detuned saws
whose low-pass snaps open and slowly closes, over a sub drop. It rings into a dark hall for about
1.5 s and fades to silence by 4.0 s.
Master: true peak <= -1 dBTP. Verify the hit's energy peak is within one frame of 75, and report
loudness and true peak from ffmpeg ebur128.
```

To reverse a cymbal or any recording yourself, ffmpeg's [areverse](https://ffmpeg.org/ffmpeg-filters.html#areverse) filter flips audio end to end.

## Why does sudden silence work in horror?

Silence is a sound effect. After a long build, cutting everything off denies the audience the payoff they're braced for. Their attention sharpens, and anything that happens next, even a quiet sound, lands harder.

A **jump scare** is a horror technique that startles the audience with a sudden creepy face or object, usually with a loud sound, often at a point where the soundtrack has gone quiet ([Wikipedia](https://en.wikipedia.org/wiki/Jump_scare)).

Practical tips for using silence:

1. **Cut, don't fade.** A hard cut to silence is more startling than a fade.
2. **Cut mid-beat.** Stopping a heartbeat or pulse partway through a cycle feels wrong in a useful way.
3. **Keep it short.** A second or two of silence is often enough on social video; longer works in film.
4. **Follow with something small.** One distant thud, a breath or a creak after the silence can be scarier than a loud hit.

## How do you pace a tension build in an edit?

Work backwards from the scare:

- Mark the frame of the payoff (the hit, the reveal, or the cut to silence).
- Put the start of the build 8 to 12 seconds earlier for a short video, longer for film.
- Line up accelerating elements so they peak just before the payoff.
- Leave a gap of a few frames before a hit so it has room.

Risers are useful here; Opus Sounds Directory has a [risers category](https://opussounds.directory/c/risers) with tension builds you can drop in under the shot, each showing its prompt, Python code, spectrogram and measured loudness. Every sound on the site is labelled as Claude Opus 5.5 output.

## How loud should horror sound effects be?

Loud enough to startle, without clipping. The contrast between quiet and loud matters more than how loud the peak is:

- Leave headroom for the biggest hit by keeping the build quieter than you think.
- Keep sub-bass in mono so it translates to phone speakers and doesn't smear.
- Limit to a true peak around -1 dBTP.
- Measure the full mix with ffmpeg's [ebur128 filter](https://ffmpeg.org/ffmpeg-filters.html#ebur128), and normalize the finished video with [loudnorm](https://ffmpeg.org/ffmpeg-filters.html#loudnorm) if your platform needs a specific target.

Remember that platforms normalize playback. A mix that is squashed loud all the way through gets turned down, and the scare loses its contrast.

## Where else can I find horror sounds?

- The [BBC Sound Effects archive](https://sound-effects.bbcrewind.co.uk/) has a large library of recordings, free for personal or educational use, with licensing for other uses.
- [Freesound](https://freesound.org) has many creaks, drones and field recordings under per-sound Creative Commons licenses.
- [Pixabay sound effects](https://pixabay.com/sound-effects/) are covered by the [Pixabay Content License](https://pixabay.com/service/license-summary/).
