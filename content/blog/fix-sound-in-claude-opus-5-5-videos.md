---
title: "How to Fix the Sound in Claude Opus 5.5 Videos (Music, SFX, Voice and Loudness)"
slug: "fix-sound-in-claude-opus-5-5-videos"
description: "Why Opus 5.5 videos often sound generic, harsh or out of sync, and the fixes creators share: constrained music prompts, measured beats, voice-first timing."
date: "2026-10-06"
keywords: ["Claude Opus 5.5 video sound", "Opus 5.5 video music sounds the same", "add music to Claude Code video", "Claude Code video sound effects", "Remotion audio sync", "AI video voiceover robotic"]
faq:
  - q: "Why does every Opus 5.5 video sound the same?"
    a: "Left without constraints, Opus 5.5 tends to write similar code-synthesized music with default tempos, chords and simple oscillators, so many videos share one sound. Naming tempo, key, instruments and a reference fixes most of it."
  - q: "Can Claude Opus 5.5 hear the audio it makes?"
    a: "No. Opus 5.5 writes the code that renders sound but cannot listen to the result, so it checks audio with measurements such as beat detection, loudness meters, spectrograms and Whisper transcripts, and a human still needs to listen."
  - q: "How do I sync sound effects to a Claude-made video?"
    a: "Put every visual event and every sound on one shared timeline in seconds or frames, generate the voiceover first, measure the beats of any music track, and place each effect on the frame of the event it belongs to."
  - q: "How loud should the audio be in an Opus 5.5 video?"
    a: "A common target for social and YouTube is about -14 LUFS integrated with a true peak at or below -1 dBTP, with music ducked well under any voiceover. Measure with ffmpeg rather than trusting the model's report."
  - q: "Should I use code-generated music or a music model for Claude videos?"
    a: "Use code-generated sound for short, frame-exact effects like hits, risers and UI sounds, and use a supplied track or a music model when you want a full, musical score, letting Opus handle the timing either way."
---

# How to Fix the Sound in Claude Opus 5.5 Videos (Music, SFX, Voice and Loudness)

To fix the sound in a Claude Opus 5.5 video, give the model hard musical constraints instead of a mood, generate the voiceover before the animation, and make it measure the audio (beats, loudness, length), because it cannot hear what it renders. Then use code-synthesized sound only for short timed effects, bring in a real track or music model for the score, and mix to a loudness target such as -14 LUFS.

This guide collects what creators report about the sound in Opus 5.5 videos and what they tell each other to do about it.

## How are Opus 5.5 videos actually made?

An Opus 5.5 video is code, not generated pixels. In Claude Code the model writes an animation in HTML, Canvas, three.js or Remotion, a headless browser renders each frame, and ffmpeg encodes the frames and audio to MP4, as the [opus5video.com guide](https://opus5video.com/how-to-make-videos-with-claude/) explains.

The audio comes from one of three places. Many videos synthesize music and effects in code with the Web Audio API or numpy. Others call ElevenLabs for voice, music or effects. Music videos usually start from a Suno song, the way the open-source [PDoomVideo](https://github.com/JohnHeibel/PDoomVideo) project did.

**Code-synthesized audio** is sound produced by a program that calculates every sample (oscillators, noise, envelopes) instead of playing back a recording.

## What goes wrong with the sound?

Five complaints come up again and again.

1. **The music all sounds alike.** "The music in every Opus motion video sounds the same," [Tony Dinh wrote](https://x.com/tdinh_me/status/2103735578537988233), and the replies agreed. [Others asked](https://x.com/aenuio/status/2104060361427296446) the same question.
2. **The effects feel cheap or busy.** One creator said the motion graphics are nailed but ["the sound effects are cheap and sound awful"](https://x.com/markksantos/status/2103559676512092356). [Another](https://x.com/itookdopamine/status/2105016360644620364) found them "too much and too annoying."
3. **Nobody in the loop can hear.** Opus wrote three scores for one ad because ["it can't hear"](https://x.com/thinkszyg/status/2104527769392799961), and [one builder summed it up](https://x.com/nosugarnoBS/status/2107124315435229297) as "my ears are the QA dept."
4. **Voiceovers sound robotic.** A one-shot launch video looked great, but ["voiceover is still robotic"](https://x.com/iam_andrearod/status/2104608503675400637).
5. **Audio and picture drift apart.** One builder spent a weekend on ["audio and video clips refusing to line up"](https://x.com/sunilkumar_ai/status/2107158704122651127). Tools can add bugs of their own, like this [Remotion Player audio/video offset issue](https://github.com/remotion-dev/remotion/issues/11439).

Plenty of people like the sound design too. The complaints are mostly about sameness, density and mix.

## Why does every Opus 5.5 video sound the same?

Left without constraints, the model falls back on defaults. [One reply](https://x.com/lachu536/status/2103849813980938732) put it plainly: "Left open it lands on 120bpm in C every time." [Another](https://x.com/Meffysto69/status/2103955813702197714) traced the sameness to General MIDI-style notes played through a basic synth.

The fix people share is to give constraints, not vibes: tempo, key, time signature, instrument count, sections that match the scenes, and one rule to break.

Here is a score prompt built on that advice:

```text
Write the score for a 30 s product video at 30 fps (900 frames).
Output: one WAV, 48 kHz / 24-bit / stereo, exactly 1440000 samples.
Tempo 96 BPM, key F# minor, 4/4. Max four instruments: muted pluck,
sub bass, brushed kit, airy pad. No pure sine leads, no I-V-vi-IV.
Sections: frames 0-180 sparse intro; 180-720 groove; 720-810 lift;
810-900 resolve to silence on the final frame.
Add human timing: +/-8 ms swing on hats, velocity variation on every note.
Render stems separately, then mix with light reverb and sidechain from the kick.
You cannot listen, so verify: exact length, -14 LUFS integrated,
true peak <= -1 dBTP (ffmpeg ebur128), and render a spectrogram.
Report the numbers and fix anything that fails.
```

If code-written music still feels thin, swap the engine instead of rewording the prompt. Creators suggest rendering a written score through a real soundfont, asking for physically modeled instruments, or [making the music with a music model and letting Opus handle timing and cuts](https://x.com/FlorianRau/status/2103814404571640077).

## How do you check audio when the model can't hear it?

Make it measure. [One builder's session](https://x.com/ivanfioravanti/status/2106334129730289678) had it check voiceover pronunciation by transcribing the clips with Whisper, and [others watched it](https://x.com/rohit3a/status/2102475769079541827) inspect spectrograms of its own effects.

Useful checks to request:

- **Beat grid.** Decode any supplied track with [librosa](https://librosa.org/doc/latest/index.html), save beats and onsets to a JSON file, and have the animation read it. [Zhu Ermu's write-up](https://zhuermu.com/en/blog/opus-5-5-five-videos/) describes it well: it could not hear the song, so it measured it.
- **Repetition score.** [Huy Tieu's release-video skill](https://huytieu.com/blog/release-video-skill-opus-5-5/) compares short windows of each candidate bed to score how much it repeats itself.
- **Loudness and length.** Measure the final mix with ffmpeg, not the model's estimate.

A **beat grid** is a list of timestamps for every beat in a track, used to place cuts and hits exactly on the music.

Then listen yourself on a phone speaker. Measurements catch errors; they don't judge taste.

## How do you sync voiceover, music and sound effects?

Generate the voice first and time the picture to it. "What cut the most back and forth was timing every scene off the real audio length instead of guessing," [one creator wrote](https://x.com/kabelsalat_info/status/2103919138175693276). Word timestamps from Whisper or a TTS timestamp endpoint let a visual fire on the exact word, as the [dev.to build log](https://dev.to/peter/this-video-is-about-how-this-video-was-made-42hl) shows.

For effects, tie each sound to an on-screen event. Huy Tieu gave each animated element a sound cue so "a card that pops in makes a pop." Keep effects sparse and quiet.

Here is an effects prompt that follows that rule:

```text
Make the SFX track for a 15 s UI demo at 30 fps (450 frames).
Output: one WAV, 48 kHz / 16-bit / stereo, exactly 720000 samples.
Read cues.json: [{"frame": 42, "type": "card_in"}, {"frame": 96, "type": "toggle"},
{"frame": 210, "type": "success"}, {"frame": 330, "type": "whoosh_out"}].
One sound per cue, nothing else. Each effect under 400 ms except whoosh_out (600 ms).
Soft transients, no harsh highs above 10 kHz, no clicks at start or end.
Effects sit 10 dB under the music bed. Peak <= -1 dBTP.
Verify every onset lands within 1 ms of its cue frame and report the offsets.
```

You can compare these with ready-made, frame-timed examples such as the [8-second tension riser](https://opussounds.directory/e/riser-tension-8s) and the [heavy impact drop](https://opussounds.directory/e/drop-impact-heavy) on Opus Sounds Directory, which publish the prompt, the code and the measured loudness for each sound.

[Heavy impact drop](/e/drop-impact-heavy)

## How loud should the music and voice be?

Aim for about -14 LUFS integrated with a true peak at or below -1 dBTP for social and YouTube, and duck the music well under any voice. [This guide](https://blog.cosine.ren/en/post/opus-5-5-motion-video-resources/) ducks the background music automatically under voice and normalizes every episode to the same loudness.

**Ducking** means automatically lowering the music while someone speaks, then bringing it back up in the gaps.

You can normalize a finished mix with ffmpeg's [loudnorm filter](https://ffmpeg.org/ffmpeg-filters.html#loudnorm), then measure it again to confirm.

## Which audio sources work best with Opus 5.5 videos?

Mix sources by job. For voice, creators most often praise ElevenLabs over default local TTS. For short timed effects, [ElevenLabs sound effects](https://elevenlabs.io/sound-effects), [Freesound](https://freesound.org), [Pixabay sound effects](https://pixabay.com/sound-effects/) and Opus Sounds Directory are all options, each with its own license terms.

Keep a manifest of where every file came from. One product-video skill [had to drop its original effects](https://www.orcarouter.ai/blog/claude-opus-5-5-product-video-skill) because nobody had recorded which library each clip came from.

## FAQ

### Why does every Opus 5.5 video sound the same?

Left without constraints, Opus 5.5 tends to write similar code-synthesized music with default tempos, chords and simple oscillators, so many videos share one sound. Naming tempo, key, instruments and a reference fixes most of it.

### Can Claude Opus 5.5 hear the audio it makes?

No. Opus 5.5 writes the code that renders sound but cannot listen to the result, so it checks audio with measurements such as beat detection, loudness meters, spectrograms and Whisper transcripts, and a human still needs to listen.

### How do I sync sound effects to a Claude-made video?

Put every visual event and every sound on one shared timeline in seconds or frames, generate the voiceover first, measure the beats of any music track, and place each effect on the frame of the event it belongs to.

### How loud should the audio be in an Opus 5.5 video?

A common target for social and YouTube is about -14 LUFS integrated with a true peak at or below -1 dBTP, with music ducked well under any voiceover. Measure with ffmpeg rather than trusting the model's report.

### Should I use code-generated music or a music model for Claude videos?

Use code-generated sound for short, frame-exact effects like hits, risers and UI sounds, and use a supplied track or a music model when you want a full, musical score, letting Opus handle the timing either way.
