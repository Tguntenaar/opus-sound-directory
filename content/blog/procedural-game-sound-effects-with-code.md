---
title: "How to Make Procedural Game Sound Effects with Code (sfxr, Web Audio and Python)"
slug: "procedural-game-sound-effects-with-code"
description: "Make game sound effects with code: sfxr-style tools, Web Audio, Python and engine APIs, plus copyable prompts for jump, coin, hit and UI sounds."
date: "2026-10-06"
keywords: ["procedural sound effects", "game sound effects generator", "sfxr", "jsfxr", "8-bit sound effects", "generate game sfx with code"]
faq:
  - q: "What is procedural audio?"
    a: "Procedural audio is sound generated at runtime or render time from code and parameters, such as oscillators, noise and envelopes, instead of played back from recordings."
  - q: "What is sfxr?"
    a: "sfxr is a small tool by DrPetter, made for the 10th Ludum Dare in December 2007, that generates retro game sound effects from a few parameters and presets."
  - q: "Are there free browser tools for game sound effects?"
    a: "Yes. jsfxr is an HTML5 port of sfxr, Bfxr is an open-source tool based on sfxr, and ChipTone is a free sound effect generator by SFBGames."
  - q: "Can I generate sounds inside Unity?"
    a: "Yes. Unity's AudioClip.Create lets you create a clip from sample data, including a streamed clip whose callback generates data on the fly."
  - q: "Where can I get free game sound effects?"
    a: "Kenney's game assets are released as CC0, OpenGameArt hosts community audio under various licenses, and you can synthesize your own with code."
---

# How to Make Procedural Game Sound Effects with Code (sfxr, Web Audio and Python)

To make game sound effects with code, start from a simple recipe (an oscillator or noise source, a pitch sweep, and a volume envelope) and render it with a tool like jsfxr, the Web Audio API in the browser, Python with numpy, or your engine's audio API. Change a few numbers and you get a jump, a coin, a laser or a hit, each in a few lines.

Procedural sounds are small, consistent and easy to vary. That suits jams, prototypes and retro styles especially well.

## What is procedural audio?

**Procedural audio** is sound generated from code and parameters (oscillators, noise, filters, envelopes) at runtime or render time, rather than played back from recorded files.

Two related terms:

- An **oscillator** is a signal source that repeats a waveform, such as a sine, square, triangle or sawtooth, at a set frequency.
- A **pitch sweep** (or slide) changes an oscillator's frequency over time, which is what makes a jump go "bwoop" upward or a laser go "pew" downward.

## Which tools generate game sound effects quickly?

**sfxr.** DrPetter made [sfxr](https://www.drpetter.se/project_sfxr.html) for the 10th Ludum Dare competition in December 2007, so jam entrants could get basic sound effects in without hunting for them. You press a randomize button or a button for a standard sound type, listen, and export the ones you like to WAV.

**jsfxr.** [jsfxr](https://sfxr.me) is an HTML5 port of sfxr that runs in the browser. Its [GitHub repo](https://github.com/chr15m/jsfxr) shows how to use it as a JavaScript library, so you can generate sounds inside a web game.

**Bfxr.** [Bfxr](https://www.bfxr.net) is an open-source tool based on sfxr, with more waveforms and controls.

**ChipTone.** [ChipTone](https://sfbgames.itch.io/chiptone) is a free sound effect generator by SFBGames, mainly for games, now in HTML5.

## How do I make game sounds with the Web Audio API?

The [Web Audio API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API) builds sounds from nodes. An [OscillatorNode](https://developer.mozilla.org/en-US/docs/Web/API/OscillatorNode) gives you a waveform, a gain node shapes the volume, and [exponentialRampToValueAtTime](https://developer.mozilla.org/en-US/docs/Web/API/AudioParam/exponentialRampToValueAtTime) creates natural-sounding sweeps and decays.

A coin pickup in a few lines:

```javascript
const ctx = new AudioContext();
function coin() {
  const t = ctx.currentTime;
  const osc = ctx.createOscillator();
  const gain = ctx.createGain();
  osc.type = "square";
  osc.frequency.setValueAtTime(988, t);         // B5
  osc.frequency.setValueAtTime(1319, t + 0.08); // E6, second note
  gain.gain.setValueAtTime(0.25, t);
  gain.gain.exponentialRampToValueAtTime(0.001, t + 0.3);
  osc.connect(gain).connect(ctx.destination);
  osc.start(t);
  osc.stop(t + 0.3);
}
```

Browsers require a user gesture (a click or key press) before audio can start, so call `coin()` from an input handler.

## How do I generate sounds in a game engine?

In Unity, [AudioClip.Create](https://docs.unity3d.com/ScriptReference/AudioClip.Create.html) builds a clip from sample data you provide. You can also create a streamed clip whose callback generates data on the fly, which is how you'd do runtime synthesis.

For any engine, the simplest route is to render WAV files offline with code and import them like normal assets. You keep the generator script in the repo, so changing a sound means editing a number and re-rendering.

## What does a good prompt for a game sound look like?

If you ask an LLM to write the synthesis code, give it the waveform, pitch path, envelope and exact length. These prompts render WAVs with Python. The first is a jump sound:

```text
Make a 0.25 s retro jump sound for a 2D platformer.
Output: one WAV, 48 kHz / 16-bit / mono, exactly 12000 samples.
Python + numpy/scipy only. Synthesise everything (no samples, no downloads). Fixed random seed.
Sound: square wave (25% duty cycle) sweeping 220 Hz -> 660 Hz on an exponential curve over 180 ms,
2 ms attack, linear decay to silence by 250 ms. Light low-pass at 6 kHz to soften the edges.
Master: true peak <= -1 dBTP.
Verify: print the sample count, measure true peak with ffmpeg ebur128, render a spectrogram.
Fix and re-render until every check passes.
```

A heavier hit or explosion, close to this entry on Opus Sounds Directory:

[Heavy impact drop](/e/drop-impact-heavy)

```text
Make a 1.2 s explosion/hit for a game.
Output: one WAV, 48 kHz / 16-bit / stereo, exactly 57600 samples.
Python + numpy/scipy only. Synthesise everything. Fixed random seed.
Sound: white noise burst through a low-pass sweeping 8 kHz -> 300 Hz over 600 ms, plus a sine
thump sweeping 120 Hz -> 40 Hz in 200 ms. 1 ms attack, exponential decay, slight stereo width
on the noise only. Ends at exactly 0.
Master: true peak <= -1 dBTP. Verify with ffmpeg ebur128 and report the numbers.
```

For menu and UI feedback in a game, the same structure works. These two entries are a matched pair:

[Success chime](/e/ui-success-chime)

[Soft error tap](/e/ui-error-soft)

Each entry shows its prompt, Python code, spectrogram and measured loudness. The success chime was the directory's first sound generated by Claude Opus 5.5, and every entry is now Opus 5.5 output: the model writes the Python code that renders each sound.

## How do I stop procedural sounds from getting repetitive?

Players hear the same footstep or gunshot hundreds of times, so add small variation at play time:

- **Pitch:** randomize by a few percent per play.
- **Volume:** vary by a decibel or two.
- **Timbre:** pick from 3 to 5 pre-rendered variants with different seeds.
- **Timing:** for rapid repeats, add a few milliseconds of jitter.

Keep a fixed seed per variant so your builds stay reproducible.

## Where can I get free game sounds if I don't want to make them?

[Kenney](https://kenney.nl/assets/category:Audio) publishes game assets, including audio packs. Its [support page](https://kenney.nl/support) says assets on its asset pages are public domain (CC0) and usable in commercial projects. [OpenGameArt](https://opengameart.org) hosts community-made audio under various licenses. [Freesound](https://freesound.org) has many game-ready effects, each with its own Creative Commons license.

The directory also has two CC0 game cues you can download as they are or re-render from their code:

[Retro coin pickup](/e/game-coin-pickup)

[Chiptune level up](/e/game-level-up)
