---
title: "Synthwave and 8-Bit Music for Videos: What Makes the Sound and How to Make It"
slug: "synthwave-and-8-bit-music-for-videos"
description: "The ingredients of synthwave and chiptune, gated reverb, and how to make retro cues, coin pickups and level-up sounds."
date: "2026-10-06"
keywords: ["synthwave music for videos", "8-bit music", "chiptune music", "retro game sound effects", "coin pickup sound effect", "level up sound effect"]
faq:
  - q: "What makes music sound like synthwave?"
    a: "Analog-style synth pads and saw basses, a steady 80s drum machine beat, big gated-reverb snares, arpeggios, and minor-key progressions at around 80 to 120 BPM."
  - q: "What is 8-bit or chiptune music?"
    a: "Chiptune is music made with, or imitating, the programmable sound generator chips in vintage consoles and computers, using a few simple pulse, triangle and noise channels."
  - q: "Where can I find free synthwave music for videos?"
    a: "Pixabay has a synthwave music search under its content license, and the YouTube Audio Library has tracks for YouTube videos; check each track's terms."
  - q: "How do I make a retro coin or level-up sound?"
    a: "Use a pulse wave playing two quick rising notes for a coin, or a fast major arpeggio ending on a held chord for a level-up, with stepped volume fades."
  - q: "What is gated reverb?"
    a: "Gated reverb is a big reverb on a drum, usually the snare, that is cut off abruptly by a noise gate, giving a large but short sound common in 1980s pop."
---

# Synthwave and 8-Bit Music for Videos: What Makes the Sound and How to Make It

Synthwave gets its sound from 80s-style synth pads and saw basses, arpeggios, a drum-machine beat with big gated-reverb snares, and minor-key chord loops. 8-bit or chiptune music uses only a few simple channels (pulse waves, a triangle and noise), which is why a coin pickup or level-up jingle sounds instantly "retro game".

Both styles are easy to recognize in a few seconds, which makes them useful for intros, gaming videos and nostalgic edits.

## What is synthwave?

**Synthwave** is electronic music styled after 1980s film, TV and game soundtracks, built on analog-style synthesizers and drum machines.

Typical ingredients:

- **Chords:** minor-key loops such as Am, F, C, G (i-VI-III-VII).
- **Tempo:** often around 80 to 120 BPM, with a driving, steady feel.
- **Bass:** a saw bass in eighths or sixteenths, often bouncing octaves.
- **Pads:** wide, detuned, slowly filtered.
- **Drums:** drum-machine kicks and hats, plus big gated snares and toms.
- **Lead:** a simple hook with portamento (glide) and delay.

## What is gated reverb?

**Gated reverb** is a large reverb on a drum, usually the snare, that a noise gate cuts off abruptly, so the hit sounds huge but stops short.

Wikipedia's [gated reverb](https://en.wikipedia.org/wiki/Gated_reverb) article credits Steve Lillywhite and Hugh Padgham with bringing it to mainstream attention around 1979, and notes it became common in 1980s pop. MusicTech has a [walkthrough for making vintage gated-reverb drums](https://musictech.com/tutorials/tips/how-to-create-authentic-vintage-drum-gated-reverb-for-synthwave-chillwave-music-styles/) for synthwave and chillwave.

## How do I make a synthwave cue that fits a video?

Plan sections in bars. At 100 BPM, one bar of 4/4 lasts 2.4 seconds, so a 20-second cue is about eight bars. Put the chorus on a cut and the final hit near the end, leaving a short tail.

Here's a 20-second cue whose chorus lands on frame 300 (10 s) and final hit on frame 570 (19 s):

[Synthwave night drive](/e/synthwave-drive-20s)

```text
Write Python (numpy/scipy only, no samples) that renders a 20-second synthwave cue.
Output: one WAV, 48 kHz / 16-bit / stereo, exactly 960000 samples. Fixed random seed.
Music: A minor at 100 BPM, chords Am-F-C-G. Frame 0 (30 fps) is a triplet pickup: a big
gated-reverb snare with a tom, a lower tom, then the first downbeat at 0.4 s.
Verse: octave-bouncing band-limited saw bass in sixteenths, a wide detuned pad that slowly opens,
a ping-pong 25% pulse arpeggio, kick and eighth hats. Gated snares join in bar 3, a noise riser
sweeps through bar 4, and a tom fill drops into a short breath of near-silence.
On frame 300 (10.0 s) the chorus lands: crash, four-on-the-floor kick, sixteenth hats and a
pulse-width-modulated lead hook with glide, vibrato and delay. On frame 570 (19.0 s) a final hit
(kick, gated snare, crash, wide Am stab) rings into a one-second hall tail to silence.
Only the mono kick and bass below 120 Hz. Master: -14 LUFS integrated, true peak <= -1 dBTP.
Verify length, loudness and peak with ffmpeg ebur128, and check the chorus hit is on frame 300.
```

If you'd rather use an existing track, browse [Pixabay's synthwave music](https://pixabay.com/music/search/synthwave/) or the [YouTube Audio Library](https://www.youtube.com/audiolibrary), and check each track's license terms.

## What is 8-bit or chiptune music?

**Chiptune** is music made with, or imitating, the programmable sound generator chips in vintage consoles, computers and arcade machines ([Wikipedia](https://en.wikipedia.org/wiki/Chiptune)).

Those chips offered only a few channels at once, typically:

- **Pulse waves** with a selectable duty cycle (such as 12.5%, 25% or 50%), which changes how thin or hollow the tone sounds.
- **A triangle wave** for bass.
- **A noise channel** for drums and effects.

Volume often moved in coarse steps rather than smooth fades, and composers faked echo by replaying a note quietly on a second channel a few frames later. Those limits are the sound.

## How do I make a retro coin pickup sound?

A coin pickup is two quick rising notes on a pulse wave. The classic shape is a short low note followed by a held note a fourth higher, then a stepped fade.

[Retro coin pickup](/e/game-coin-pickup)

```text
Write Python (numpy/scipy only) that renders a 0.5-second retro 8-bit coin pickup.
Output: one WAV, 48 kHz / 16-bit / mono, exactly 24000 samples.
Sound: a pulse-wave channel plays a short B5 on frame 0, then E6 four 60 Hz frames (67 ms) later.
E6 holds, then steps down a 16-level volume ladder, one step per 1/60 s, each step smoothed over
1 ms, to silence before 0.5 s. Build the pulse from band-limited odd harmonics below 12 kHz so it
never aliases. A second, quieter pulse channel repeats both notes six frames later as a fake echo.
Filter like an old console: high-pass at 90 Hz and 440 Hz, low-pass at 14 kHz.
Master: true peak <= -1 dBTP. Verify with ffmpeg ebur128 and report the peak.
```

## How do I make a level-up sound?

A level-up is a fast major arpeggio that climbs, pauses for a breath, then lands on a held chord. In this one, a four-channel build climbs through C, F and G and lands a C major chord on frame 45 (1.5 s):

[Chiptune level up](/e/game-level-up)

Other retro touches that work in short video: a lower, falling version for "game over", a single noise burst for a hit, and a short arpeggio for menu selections. The [sfxr.me](https://sfxr.me) generator has quick presets such as pickup/coin and power-up, handy for sketching ideas.

## How do I make 8-bit effects sound right in a modern mix?

- **Keep them band-limited.** Naive square waves alias, which sounds harsh rather than retro.
- **Use stepped volume.** Coarse volume steps sound authentic; smooth exponential fades sound modern.
- **Mind the low end.** Old consoles filtered out deep bass, so keep pickups and blips light.
- **Lower the level.** Bright pulse waves sound louder than their meter suggests; set them by ear against your music.

If you want an even crunchier tone, a **bitcrusher** reduces sample rate or bit depth ([Wikipedia](https://en.wikipedia.org/wiki/Bitcrusher)), and ffmpeg's [acrusher](https://ffmpeg.org/ffmpeg-filters.html#acrusher) filter does this.

## Where can I find more retro sounds?

The cues above come from Opus Sounds Directory, where every sound is labelled as Claude Opus 5.5 output: the model writes the Python that renders it, and each page shows the prompt, code, spectrogram and loudness. Its [UI sounds category](https://opussounds.directory/c/ui-sounds) has short blips and confirmations as well.

Other places to look:

- [Freesound](https://freesound.org), with per-sound Creative Commons licenses.
- [Pixabay sound effects](https://pixabay.com/sound-effects/), under the [Pixabay Content License](https://pixabay.com/service/license-summary/).
- [sfxr.me](https://sfxr.me) for making your own 8-bit effects in the browser.
