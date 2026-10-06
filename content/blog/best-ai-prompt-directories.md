---
title: "The Best Directories for AI Prompts and Assets in 2026"
slug: "best-ai-prompt-directories"
description: "A practical list of AI prompt directories and asset libraries for code, images, video and sound, and how to judge whether a prompt is worth copying."
date: "2026-10-06"
keywords: ["AI prompt directory", "best AI prompt library", "prompt directory for developers", "AI sound prompts", "Hugging Face Spaces", "cursor rules directory"]
faq:
  - q: "What is an AI prompt directory?"
    a: "An AI prompt directory is a searchable collection of prompts, rules or assets that others have written and tested, so you can copy and adapt them instead of starting from scratch."
  - q: "What is the best prompt directory for coding?"
    a: "For Cursor users, cursor.directory collects community rules and plugins by framework; prompts.chat is a broader open-source prompt collection for ChatGPT, Claude and Gemini."
  - q: "Where can I find prompts for AI sound effects and music?"
    a: "Opus Sounds Directory lists numeric sound prompts with their Python code, spectrogram and measured loudness, and Hugging Face model cards and Spaces show example prompts for text-to-audio models."
  - q: "Are prompts in directories free to use?"
    a: "Many are, but check each site's terms; open-source collections such as prompts.chat publish their license on GitHub, while marketplaces sell prompts under their own terms."
  - q: "How do I know if a prompt is good?"
    a: "Prefer prompts that show the output they produced, state the model and date, and use specific numbers or constraints you can change."
---

# The Best Directories for AI Prompts and Assets in 2026

The most useful AI prompt directories are the ones tied to a specific job: cursor.directory for coding rules, prompts.chat for general chat prompts, Hugging Face for models, Spaces and datasets, Civitai and OpenArt for image work, and niche directories such as Opus Sounds Directory for sound prompts. Pick by the output you need, then favor entries that show the result next to the prompt.

A prompt without its output is a guess. A prompt with its output, model name and date is something you can test.

## What is an AI prompt directory?

An **AI prompt directory** is a searchable collection of prompts, rules or assets that other people have written and tested, so you can copy and adapt them instead of starting from scratch.

Some directories store plain text prompts. Others store full assets: model weights, demo apps, sample outputs, or code. The best ones attach enough context (model, settings, result) that you can reproduce what you see.

## Which prompt directories are best for coding?

**[cursor.directory](https://cursor.directory)** collects community rules and plugins for the Cursor editor, organized by framework and language (Next.js, Python, Flutter and many more), along with MCP server listings. If you write code with an AI editor, it is a fast way to find a starting rule set for your stack.

**[prompts.chat](https://prompts.chat)** (formerly Awesome ChatGPT Prompts) is a community prompt collection for ChatGPT, Claude, Gemini and other assistants. Its source is open on [GitHub](https://github.com/f/prompts.chat), and you can self-host it.

For model-specific technique rather than ready-made prompts, Anthropic's [prompting best practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/overview) guide is a good reference for Claude models, including [Claude Opus 5.5](https://www.anthropic.com/claude-opus-5-5).

## Where do I find AI models, demos and datasets?

**Hugging Face** is the main hub. Three parts matter most:

- **[Models](https://huggingface.co/models?pipeline_tag=text-to-audio)**: filter by task, for example text-to-audio or [text-to-video](https://huggingface.co/models?pipeline_tag=text-to-video). Model cards often include example prompts and license terms.
- **[Spaces](https://huggingface.co/spaces)**: hosted demo apps where you can try a model in the browser, such as the [MusicGen Space](https://huggingface.co/spaces/facebook/MusicGen) or the [video generation category](https://huggingface.co/spaces?category=video-generation).
- **[Datasets](https://huggingface.co/datasets)**: training and evaluation data, useful if you want to see what prompts and captions a model learned from.

The [text-to-video task page](https://huggingface.co/tasks/text-to-video) is a good primer if you're new to the category.

## Which directories are best for image and video prompts?

**[Civitai](https://civitai.com)** hosts community models (including Stable Diffusion and Flux fine-tunes) with example images and the prompts and settings that produced them.

**[OpenArt](https://openart.ai)** is a generation platform for images, video and audio that also shows community creations with their prompts.

**[Lexica](https://lexica.art)** is an AI image generation and search site, useful for browsing visual styles before you write your own prompt.

For video, prompt guides from model makers are often more useful than third-party lists. Google's [Veo docs](https://ai.google.dev/gemini-api/docs/veo) show how to describe camera moves, dialogue and sound in one prompt.

## Where can I find sound and music prompts?

Sound is the least-covered category. Three useful places:

- **Opus Sounds Directory** is a free directory of sound effects and music beds for video (ad beds by length, drops, risers, UI sounds, logo stings, ambient and chaos-to-calm beds). Each entry shows the numeric prompt, the Python synthesis code, a spectrogram and measured loudness, so you can see whether a render hit its targets. Most current entries are local numpy synthesis written to Opus-style prompts, and each entry page states how it was made.
- **Hugging Face model cards** for audio models such as [MusicGen](https://huggingface.co/facebook/musicgen-large) and [Stable Audio Open 1.0](https://huggingface.co/stabilityai/stable-audio-open-1.0) include example text prompts.
- **Recorded sound libraries** such as [Freesound](https://freesound.org) and [Pixabay sound effects](https://pixabay.com/sound-effects/) aren't prompt directories, but their tags and descriptions are a good vocabulary source when you describe a sound.

Here is a sound prompt in the style you'll find there, based on the [Bright logo sting](https://opussounds.directory/e/logo-sting-bright) entry:

```text
Make a 2.5 s logo sting for video at 30 fps.
Output: one WAV, 48 kHz / 16-bit / stereo, exactly 120000 samples.
Python + numpy/scipy only. Synthesise everything (no samples, no downloads). Fixed random seed.
Sound: major chord bloom (C-E-G-B, soft attack 30 ms) with a shimmer tail; logo appears at frame 0,
sparkle accent at frame 60 (sample 96000); tail decays to exactly 0 by the last sample.
Master: true peak <= -1 dBTP; leave headroom for a voiceover.
Verify length and peak with ffmpeg ebur128, render a spectrogram, and report the numbers.
```

And one for an ambient bed, similar to the [Lo-fi ambient bed](https://opussounds.directory/e/ambient-bed-lofi) entry:

```text
Make a 12 s loopable ambient bed for video at 30 fps.
Output: one WAV, 48 kHz / 16-bit / stereo, exactly 576000 samples.
Python + numpy/scipy only. Synthesise everything. Fixed random seed.
Sound: warm detuned saw pads through a low-pass at 2 kHz, faint vinyl-like crackle noise at -30 dB
relative to the pad, very slow filter movement (one cycle per 12 s) so the end matches the start.
Loop check: the last 50 ms must crossfade cleanly into the first 50 ms.
Master: -14 LUFS integrated, true peak <= -1 dBTP. Verify with ffmpeg ebur128 and report.
```

## How do I judge whether a prompt is worth copying?

Use a quick checklist before you trust any directory entry:

1. **Is the output shown?** A prompt next to its image, audio or code beats a prompt alone.
2. **Is the model named, with a date?** Models change. A prompt tuned for one model may not transfer.
3. **Is it specific?** Numbers and constraints (length, size, format, timing) make prompts reusable.
4. **Is the license clear?** Check what you can do with both the prompt and the output.
5. **Can you change one variable?** Good prompts have obvious knobs, such as key, tempo or duration.

**Reproducibility** means another person can run the same prompt with the same model and settings and get the same or a very similar result.

## FAQ

### What is an AI prompt directory?

An AI prompt directory is a searchable collection of prompts, rules or assets that others have written and tested, so you can copy and adapt them instead of starting from scratch.

### What is the best prompt directory for coding?

For Cursor users, cursor.directory collects community rules and plugins by framework; prompts.chat is a broader open-source prompt collection for ChatGPT, Claude and Gemini.

### Where can I find prompts for AI sound effects and music?

Opus Sounds Directory lists numeric sound prompts with their Python code, spectrogram and measured loudness, and Hugging Face model cards and Spaces show example prompts for text-to-audio models.

### Are prompts in directories free to use?

Many are, but check each site's terms; open-source collections such as prompts.chat publish their license on GitHub, while marketplaces sell prompts under their own terms.

### How do I know if a prompt is good?

Prefer prompts that show the output they produced, state the model and date, and use specific numbers or constraints you can change.
