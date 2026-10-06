---
title: "How Long Should a Podcast Intro Be? How to Make Podcast Intro Music"
slug: "podcast-intro-music"
description: "Intro length, planning a theme in bars so it ends on time, licensed sources, and Apple's -16 LKFS loudness guidance."
date: "2026-10-06"
keywords: ["podcast intro music", "how long should a podcast intro be", "how to make a podcast intro", "podcast theme music", "podcast intro music free", "podcast loudness LUFS"]
faq:
  - q: "How long should podcast intro music be?"
    a: "Short. A music-only intro of roughly 10 to 20 seconds is a common choice, and a sting before the host speaks can be just a few seconds; long intros get skipped."
  - q: "Where can I get free podcast intro music?"
    a: "Pixabay music, Incompetech (free with credit under Creative Commons) and the YouTube Audio Library for video podcasts on YouTube are common sources; check each license for podcast use."
  - q: "How loud should a podcast be?"
    a: "Apple Podcasts recommends an overall loudness around -16 LKFS with a 1 dB tolerance and true peak no higher than -1 dBFS, measured per ITU-R BS.1770."
  - q: "Should the intro music play under the host's voice?"
    a: "Many shows let the music end on a clear final chord or duck it well below the voice as the host starts, so the first words are easy to hear."
  - q: "How do I make an intro end exactly on time?"
    a: "Plan it in bars. At a given tempo each bar has a fixed length, so you can place the final chord on an exact second and leave a tail for the host to start talking."
---

# How Long Should a Podcast Intro Be? How to Make Podcast Intro Music

Keep podcast intro music short: roughly 10 to 20 seconds for a music-led intro, or a few seconds for a sting right before the host speaks. Plan the music in bars so its final chord lands on a known second, leave a short tail for the first words, and master the episode to your platform's loudness target, such as Apple's -16 LKFS.

The intro's job is to tell listeners they're in the right place, then get out of the way.

## What is podcast intro music?

**Podcast intro music** is a short, recurring piece that opens each episode, sets the show's tone and makes it recognizable by ear.

A **sting** is a very short musical phrase, often a few seconds long, used to open a show, mark a segment change or punctuate a moment.

A **music bed** is background music played under speech, such as under the host's welcome or a sponsor read.

## How long should a podcast intro be?

Shorter than you think. Many guides land on about 10 to 20 seconds for a music-only intro. The Podcast Host's [look at the intros of top-charting podcasts](https://www.thepodcasthost.com/business-of-podcasting/podcast-intro-formula/) found shorter intros trending, with several popular shows using no intro at all beyond a brief jingle.

A useful rule: if the intro would annoy you on the twentieth listen, cut it down. Listeners hear it every episode.

## How do I make the intro end exactly on time?

Plan it in bars, not seconds. In 4/4 time, one bar lasts 4 × 60 / BPM seconds:

| Tempo | One bar | Four bars |
|---|---|---|
| 90 BPM | 2.67 s | 10.67 s |
| 96 BPM | 2.5 s | 10 s |
| 120 BPM | 2 s | 8 s |

At 96 BPM, four bars fill exactly 10 seconds. You can end the melody on a chord near the 8-second mark and let it ring out to 10 seconds, leaving a natural gap for the host.

A **ritardando** is a gradual slowing of tempo, often used to make a final chord feel settled. Wikipedia covers it under [ritardando](https://en.wikipedia.org/wiki/Ritardando). A slight slow-down into the last chord sounds human, but if you use one, plan the last chord's exact time so the edit still lines up.

## What should podcast intro music sound like?

It should match the show, not the genre's clichés. A few practical points:

- **Pick a tempo that matches the host's energy.** A calm interview show and a fast news recap want different tempos.
- **Keep the midrange clear.** If the voice comes in over the tail, avoid busy instruments around 1 to 4 kHz.
- **Write one hummable motif.** It can come back as a segment sting and the outro.
- **End cleanly.** A clear final chord (sometimes called a "button") tells the listener the talk is about to start.

A **leitmotif** is a short recurring musical idea tied to a character or idea ([Wikipedia](https://en.wikipedia.org/wiki/Leitmotif)). A podcast theme works the same way: the same motif in the intro, segment stings and outro.

## Where can I get podcast intro music?

Start with sources whose license clearly covers podcasts:

- [Pixabay music](https://pixabay.com/music/search/podcast%20intro/) has many tracks tagged for podcast intros, under the [Pixabay Content License](https://pixabay.com/service/license-summary/).
- [Incompetech](https://incompetech.com) by Kevin MacLeod offers a free Creative Commons option that requires credit, plus a paid license without attribution, described on its [licenses page](https://incompetech.com/music/royalty-free/licenses/).
- The [YouTube Audio Library](https://www.youtube.com/audiolibrary) is a good fit if you publish the podcast as video on YouTube.
- Text-to-music tools such as [ElevenLabs Music](https://elevenlabs.io/music) or open models like [MusicGen](https://huggingface.co/facebook/musicgen-large) can sketch ideas. MusicGen's weights are CC-BY-NC 4.0, so check terms before using its output in a commercial show.

Opus Sounds Directory has a short podcast intro and several logo stings you can play and download, each with its prompt, code and measured loudness. Every sound there is Claude Opus 5.5 output: the model writes the Python synthesis code that renders it.

## What does a podcast intro prompt look like?

Give the generator the tempo, bar count, key, instruments, the exact second of the final chord, and how long the ring-out lasts. Here is the intro on the site:

[Podcast intro (warm EP)](/e/podcast-intro-10s)

A prompt in the same style you can copy and adapt:

```text
Write Python (numpy/scipy only, no samples) that renders a 10-second podcast intro.
Output: one WAV, 48 kHz / 16-bit / stereo, exactly 480000 samples. Fixed random seed.
Style: friendly small jazz trio in Bb major at 96 BPM: tine electric piano comping and a simple
swung, singable melody, walking upright-style bass, brushed snare and a soft kick.
Form: full-band hit with a brushed cymbal on frame 0 (30 fps). Bars 1-3 groove; the last bar
slows slightly into a final Bb6/9 chord that lands exactly on frame 240 (8.0 s, sample 384000).
The chord rings out to silence by 10.0 s, leaving room for the host to start talking.
Keep everything below 120 Hz mono (bass and kick only).
Master: about -16 LUFS integrated for podcast delivery, true peak <= -1 dBTP.
You can't listen, so verify: exact sample count, loudness and true peak with ffmpeg ebur128,
the energy peak of the final chord within one frame of 240, and a spectrogram. Fix until it passes.
```

And a short, warm sting for segment changes, based on this logo:

[Organic kalimba logo](/e/logo-sting-organic)

```text
Write Python (numpy/scipy only) that renders a 3-second podcast segment sting.
Output: one WAV, 48 kHz / 16-bit / stereo, exactly 144000 samples. Fixed random seed.
Sound: thumb-plucked kalimba motif in G major at 96 BPM (G4, B4, D5, E5 in eighth notes,
then back to D5), with inharmonic tine overtones near 5.9x and 17x, a soft hand-drum bass tone
and a quiet seed shaker in sixteenths. The shaker stops just before frame 48 (1.6 s) and a soft
five-note G major chord lands there and rings out in a small wooden room to silence by 3.0 s.
Master: true peak <= -1 dBTP. Verify length and peak with ffmpeg ebur128 and report the numbers.
```

You can browse more short pieces on the [logo stings](https://opussounds.directory/c/logo-stings) and [ad beds](https://opussounds.directory/c/ad-beds) category pages.

## How loud should podcast intro music be?

Match the episode's loudness so the intro doesn't jump out. Apple's [podcast audio requirements](https://podcasters.apple.com/support/893-audio-requirements) recommend keeping overall loudness around -16 LKFS with a ±1 dB tolerance, and true peak no higher than -1 dB FS, calculated per ITU-R BS.1770.

**LKFS** is the same loudness unit as LUFS, defined by ITU-R BS.1770.

Measure the full episode with ffmpeg's [ebur128 filter](https://ffmpeg.org/ffmpeg-filters.html#ebur128). If the music continues under the host, duck it with automation in your editor, or with ffmpeg's [sidechaincompress filter](https://ffmpeg.org/ffmpeg-filters.html#sidechaincompress) so the voice track pushes the music down.

## What else should a podcast music kit include?

Once the intro works, reuse its motif for a small kit:

1. **Intro** (10 to 20 s).
2. **Short sting** (2 to 4 s) for cold opens and segment breaks.
3. **Bed** (loopable, no melody) for under the welcome or sponsor reads.
4. **Outro** (a relaxed version of the theme ending on a chord).

Keep the same key and instruments across all four so the show sounds consistent.
