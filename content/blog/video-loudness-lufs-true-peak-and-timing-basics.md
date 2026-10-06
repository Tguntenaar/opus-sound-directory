---
title: "What LUFS Should Video Be? Loudness, True Peak and Timing Basics for Video"
slug: "video-loudness-lufs-true-peak-and-timing-basics"
description: "What LUFS and true peak mean for video, why -14 LUFS and -1 dBTP are common targets, how to measure with ffmpeg, and how to sync cues to fps and BPM."
date: "2026-10-06"
keywords: ["LUFS for video", "what LUFS for YouTube", "true peak -1 dBTP", "ffmpeg ebur128", "EBU R128 loudness", "sync audio to frame rate BPM"]
faq:
  - q: "What LUFS should a YouTube or social video be?"
    a: "About -14 LUFS integrated with a true peak at or below -1 dBTP is a widely used target for online video, though platforms don't all publish a fixed number and may adjust playback."
  - q: "What is the difference between LUFS and dB?"
    a: "dBFS measures signal level relative to digital full scale, while LUFS measures perceived loudness using the K-weighting and gating defined in ITU-R BS.1770."
  - q: "What is true peak?"
    a: "True peak is the estimated peak of the reconstructed analog waveform between samples, measured in dBTP, and it can be higher than the highest sample value."
  - q: "How do I measure LUFS for free?"
    a: "Run ffmpeg with the ebur128 filter, for example: ffmpeg -i mix.wav -af ebur128=peak=true -f null -, and read the integrated loudness and true peak in the summary."
  - q: "How many frames is one beat?"
    a: "Frames per beat equals fps times 60 divided by BPM, so at 30 fps one beat at 120 BPM is 15 frames and at 90 BPM is 20 frames."
  - q: "What loudness does broadcast TV use?"
    a: "EBU R128 recommends -23 LUFS integrated with a maximum true peak of -1 dBTP for broadcast in Europe."
---

# What LUFS Should Video Be? Loudness, True Peak and Timing Basics for Video

For online video, a widely used target is about -14 LUFS integrated loudness with a true peak no higher than -1 dBTP. Broadcast is quieter: EBU R128 recommends -23 LUFS. Measure the whole finished mix, not individual clips, and line up audio cues to whole video frames using the frame rate and tempo.

The rest of this post explains what those numbers mean, how to measure them for free, and how to convert between frames, beats and samples.

## What is LUFS?

**LUFS** (Loudness Units relative to Full Scale) is a unit of perceived loudness, defined by the measurement method in [ITU-R BS.1770](https://www.itu.int/rec/R-REC-BS.1770), that weights frequencies roughly the way human hearing does and ignores near-silent passages.

**LKFS** is the same unit under a different name, used mainly in North American broadcast specs.

**Integrated loudness** is the average loudness of an entire file or program, measured in LUFS with gating so silence doesn't pull the number down.

BS.1770 meters also report **momentary** loudness (a 400 ms window) and **short-term** loudness (a 3 s window), which help you spot loud moments inside a mix.

## Why is -14 LUFS the common target for online video?

Many streaming and video platforms turn down audio that is much louder than their reference, so mixing far above it mostly costs you dynamics. Around -14 LUFS integrated has become the common reference for online video and streaming.

Treat it as a starting point. Platforms don't all publish one fixed number. YouTube, for example, says it [may apply audio enhancements](https://support.google.com/youtube/answer/16619284?hl=en) such as automatic volume adjustments and Stable volume. Some editors mix short-form vertical video slightly quieter, around -16 LUFS, for phone speakers. What matters most is a clear voice, no clipping, and consistency across your uploads.

## What do EBU R128 and true peak mean?

[EBU R128](https://tech.ebu.ch/publications/r128) is the European Broadcasting Union's loudness recommendation. It sets a program target of -23 LUFS and a maximum true peak level of -1 dBTP, and adds a Loudness Range (LRA) descriptor. The full text is in the [R128 PDF](https://tech.ebu.ch/docs/r/r128.pdf).

**True peak** is the estimated maximum level of the reconstructed analog waveform, including peaks that fall between digital samples, measured in dBTP (decibels relative to full scale, true peak).

Sample peaks can read -0.3 dBFS while the true peak is above 0 dBTP. Lossy encoders (AAC, MP3, Opus) can raise peaks further, which is why -1 dBTP is a common ceiling: it leaves room for the encode.

**Loudness Range (LRA)** describes how much the loudness varies over a program, in LU. Dialogue-heavy content usually has a lower LRA than a film score.

## How do I measure LUFS and true peak with ffmpeg?

ffmpeg's [ebur128 filter](https://ffmpeg.org/ffmpeg-filters.html#ebur128) measures integrated loudness, LRA and true peak:

```bash
ffmpeg -hide_banner -nostats -i final_mix.wav -af ebur128=peak=true -f null -
```

Read the summary at the end: `I:` is integrated loudness in LUFS and the `True peak` block shows the peak in dBFS (true-peak).

To normalize toward a target, the [loudnorm filter](https://ffmpeg.org/ffmpeg-filters.html#loudnorm) implements EBU R128-style normalization. The usual approach is two passes: measure first, then apply with the measured values.

```bash
# pass 1: measure
ffmpeg -i in.wav -af loudnorm=I=-14:TP=-1:LRA=11:print_format=json -f null -
# pass 2: apply, pasting the measured_* values from pass 1
ffmpeg -i in.wav -af loudnorm=I=-14:TP=-1:LRA=11:measured_I=-18.2:measured_TP=-3.1:measured_LRA=6.4:measured_thresh=-28.5:linear=true -ar 48000 out.wav
```

The `measured_*` numbers above are placeholders. Replace them with your own pass-1 output. In Python, [pyloudnorm](https://github.com/csteinmetz1/pyloudnorm) gives the same kind of BS.1770 measurement.

## How do I convert frames, beats and samples?

Three formulas cover almost every timing job:

- **Seconds per frame** = 1 / fps
- **Samples per frame** = sample rate / fps
- **Frames per beat** = fps × 60 / BPM

At 48 kHz, samples per frame are:

| Frame rate | Samples per frame |
|---|---|
| 24 fps | 2,000 |
| 25 fps | 1,920 |
| 30 fps | 1,600 |
| 60 fps | 800 |
| 29.97 fps | 1,601.6 (not a whole number) |

Frames per beat at 30 fps:

| BPM | Frames per beat |
|---|---|
| 90 | 20 |
| 100 | 18 |
| 120 | 15 |
| 80 | 22.5 |
| 128 | 14.06 |

Tempos that give whole frames per beat (90, 100, 120 at 30 fps; 120 at 24 fps gives 12) make it easy to cut picture on the beat. Tempos like 80 or 128 BPM at 30 fps drift against the frame grid, so put hard cues on the nearest whole frame and accept a few milliseconds of offset.

A **cue frame** is the specific video frame number where an audio event (a hit, a drop, a logo sting) must land.

A countdown makes cue frames easy to hear: in this one, each pip lands exactly on a whole second (frames 0, 30, 60 and so on at 30 fps).

[Countdown 10 → 0](/e/countdown-10-to-0)

## How do I put these numbers into a sound prompt?

If you generate audio from code, write the numbers straight into the prompt. Here is a drop that lands on a fixed frame, the same structure as the [Heavy impact drop](https://opussounds.directory/e/drop-impact-heavy) entry on Opus Sounds Directory:

```text
Make a 3 s transition drop for video at 30 fps.
Output: one WAV, 48 kHz / 16-bit / stereo, exactly 144000 samples.
Python + numpy/scipy only. Synthesise everything (no samples, no downloads). Fixed random seed.
Sound: sub drop from 120 Hz to 40 Hz + short noise burst + 1.2 s tail.
Peak impact aligned to frame 45 (1.5 s, sample 72000).
Master: -14 LUFS integrated, true peak <= -1 dBTP.
Verify length, loudness and peak with ffmpeg ebur128; confirm the RMS maximum falls in frame 45;
render a spectrogram. Fix and re-render until every check passes, then report the numbers.
```

And a 30-second bed on a 90 BPM grid, which divides evenly into 20 frames per beat (compare the [Traffic glitch → warm strings](https://opussounds.directory/e/chaos-calm-02) entry):

```text
Make a 30 s music bed for a vertical video ad at 30 fps.
Output: one WAV, 48 kHz / 16-bit / stereo, exactly 1440000 samples.
Python + numpy/scipy only. Synthesise everything. Fixed random seed.
Timing: 90 BPM (1 beat = 20 frames, 1 bar = 80 frames). Cues: frame 0 = hit;
frame 320 (bar 5) = texture change; frame 800 (bar 11) = full arrangement;
last bar ends with a soft final chord that fades to exactly 0 at sample 1440000.
Sound: slow legato strings, soft sub bass, gentle pulse, key A minor.
Master: -14 LUFS integrated, true peak <= -1 dBTP.
Verify length, loudness and peak with ffmpeg ebur128 and report the numbers.
```

Opus Sounds Directory shows each entry's target next to its measured integrated LUFS and true peak, which is a handy way to see how far a render can land from the number in its prompt. Always measure the final mix yourself.

## What's a simple loudness checklist before export?

1. Mix with voice first, then bring music and effects in underneath.
2. Measure the full mix with ebur128.
3. Adjust gain toward your target (about -14 LUFS for online, -23 LUFS for EBU broadcast).
4. Keep true peak at or below -1 dBTP.
5. Check that cues land on their frames.
6. Listen on a phone and on headphones.
