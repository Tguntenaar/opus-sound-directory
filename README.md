<div align="center">

<a href="https://opussounds.directory">
  <img src="public/og-default.png" alt="Opus Sounds Directory — royalty-free sound effects and music beds, with prompts, Python code and loudness metrics" width="900">
</a>

# Opus Sounds Directory

**Find your sound. See how it was made. Make it your own.**

An open directory of synthesized sound effects, music beds and loops for videos, games and apps.

[![Browse sounds](https://img.shields.io/badge/Listen-opussounds.directory-8b5cf6?style=for-the-badge)](https://opussounds.directory) [![Sounds: CC0](https://img.shields.io/badge/Sounds-CC0_1.0-8b5cf6?style=for-the-badge)](ASSETS-LICENSE.md) [![Code: MIT](https://img.shields.io/badge/Code-MIT-8b5cf6?style=for-the-badge)](LICENSE)

[![GitHub stars](https://img.shields.io/github/stars/Tguntenaar/opus-sound-directory?style=flat&color=8b5cf6)](https://github.com/Tguntenaar/opus-sound-directory/stargazers) [![Last commit](https://img.shields.io/github/last-commit/Tguntenaar/opus-sound-directory/main?style=flat&color=8b5cf6)](https://github.com/Tguntenaar/opus-sound-directory/commits/main) [![Pull requests welcome](https://img.shields.io/badge/PRs-welcome-8b5cf6?style=flat)](CONTRIBUTING.md)

[Browse the directory](https://opussounds.directory) · [Submit a sound](https://opussounds.directory/submit) · [Read the blog](https://opussounds.directory/blog) · [Connect an AI assistant](#use-with-ai-assistants)

</div>

> [!TIP]
> **Yes, you can use the sounds commercially.** Download, edit, remix and use the audio in your own projects without permission or attribution. Sounds are **CC0**; source code is **MIT**. [Full licensing details ↓](#license)

## Contents

- [Who is this for?](#who-is-this-for)
- [Explore by category](#explore-by-category)
- [Start listening](#start-listening)
- [What comes with a sound](#what-comes-with-a-sound)
- [Use with AI assistants](#use-with-ai-assistants)
- [Run locally](#run-locally)
- [Contribute](#contribute)
- [License](#license)

## Who is this for?

Anyone making something with sound—or just playing around with video, audio and LLMs. Download a sound and use it immediately, or explore the prompt and Python code to make it your own. **No coding is required to use the audio.**

| If you’re… | Try this |
| :--- | :--- |
| **Experimenting with video, sound or LLMs** | Play with effects, ask an AI assistant for variations, and see how a prompt becomes a sound. |
| **Creating or editing videos** | Find transitions, reaction effects, cinematic hits and short background beds. |
| **Building an indie game** | Add collectible sounds, UI feedback, arcade effects and ambient loops. |
| **Designing an app or product** | Choose taps, notifications, success and error sounds for everyday interactions. |
| **Building with AI agents** | Use the skill and MCP connection to help your agent discover sounds and integrate assets. |
| **Exploring sound design or creative coding** | Inspect the synthesis code, learn techniques and create your own variations. |

## Explore by category

| Collection | Find the right moment |
| :--- | :--- |
| [UI & app sounds](https://opussounds.directory/c/ui-sounds) | Taps, toggles, notifications and feedback for product interfaces. |
| [Drops & transitions](https://opussounds.directory/c/drops) | Impacts, whooshes and accents for cuts and reveals. |
| [Game sounds](https://opussounds.directory/c/gaming) | Arcade effects, chiptune gestures and game feedback. |
| [Cinematic hits](https://opussounds.directory/c/cinematic) | Braams, booms and trailer-sized impacts. |
| [Meme & reaction](https://opussounds.directory/c/meme) | Comic fails and reaction stings. |
| [Retro tech](https://opussounds.directory/c/retro-tech) | Dial tones, modems and nostalgic machine sounds. |
| [Risers](https://opussounds.directory/c/risers) | Tension builds timed to the frame. |
| [Ambient beds](https://opussounds.directory/c/ambient) | Background textures, atmospheres and loops. |
| [Ad beds by length](https://opussounds.directory/c/ad-beds) | Short beds for bumpers, product videos and ads. |
| [Logo stings](https://opussounds.directory/c/logo-stings) | Brief musical signatures for intros and reveals. |
| [Chaos → calm](https://opussounds.directory/c/chaos-calm) | Tension that resolves into space and calm. |

## Start listening

A few entry points into the collection. Open a sound to listen and download it.

| Sound | Use it for |
| :--- | :--- |
| [Shock boom](https://opussounds.directory/e/heavy-boom-meme) | A reaction cut or sudden zoom. |
| [Pass-by whoosh](https://opussounds.directory/e/whoosh-pass-by) | A fast transition or moving object. |
| [Cozy UI sprite](https://opussounds.directory/e/ui-cozy-sprite) | A coordinated set of small product interactions. |
| [Endless Shepard riser](https://opussounds.directory/e/endless-riser-shepard) | Sustained tension without a final hit. |
| [56k modem handshake](https://opussounds.directory/e/dialup-modem-56k) | A nostalgic connection sequence. |
| [Coin pickup sparkle](https://opussounds.directory/e/game-coin-pickup) | A collectible or positive reward. |

### Behind the sound

[![Spectrogram of the shock boom](public/assets/heavy-boom-meme/spectrogram.png)](https://opussounds.directory/e/heavy-boom-meme)

*Shock boom: inspect its frequency content, read the synthesis code, then adapt it to your edit.*

## What comes with a sound

- **Audio to preview and download** — listen before choosing a file.
- **The creative prompt** — timing, character and synthesis direction.
- **Python synthesis code** — inspect how the sound is made and regenerate it.
- **Spectrograms and measurements** — duration, integrated loudness and true peak.
- **Timing and attribution** — frame cues, sample rate, generation date and model metadata.

The catalog focuses on procedural synthesis with NumPy and SciPy. Model attribution is recorded per entry; generation archives retain the provenance of experiments and candidate takes.

<details>
<summary><strong>Explore the source and candidate takes</strong></summary>

| Path | Contents |
| :--- | :--- |
| [`content/entries/`](content/entries/) | Catalog metadata, prompts and timing. |
| [`public/assets/`](public/assets/) | Published audio, synthesis scripts and spectrograms. |
| [`masters/`](masters/) | Full-rate audio masters. |
| [`runner/`](runner/) | Synthesis, mastering and verification tools. |
| [`provenance/`](provenance/) | Generation history and review candidates. |
| [Codex Hero8 collection](provenance/codex-generations/README.md) | 27 alternative takes, an offline listening page and QA reports. |

The Hero8 archive records its own selection status and Codex attribution. Candidate rankings are provisional; see its report before choosing by ear.

</details>

## Use with AI assistants

Install the **Opus Sounds skill** to help your agent find suitable audio, check duration and licensing, and integrate sounds into your app, game or video.

```bash
npx skills add Tguntenaar/opus-sound-directory --skill opus-sounds
```

Run in your project with Node.js and npm installed, then choose your agent in the installer. [Review the skill](skills/opus-sounds/SKILL.md) · [Supported agents](https://github.com/vercel-labs/skills#supported-agents).

**Connect MCP separately** for access to the live directory. No API key is needed for public read tools. Installing the skill does not register the MCP server automatically.

- **Claude Code:** `claude mcp add --transport http opus-sounds https://opussounds.directory/mcp`
- **Cursor:** merge the server entry into `.cursor/mcp.json`; see the [setup instructions](skills/opus-sounds/references/setup.md).
- **Other clients:** add `https://opussounds.directory/mcp` as a remote Streamable HTTP server using your client's configuration format.

[Website installation guide](https://opussounds.directory/agents) · [MCP tool details](https://opussounds.directory/mcp)

Try: **“Find a gentle notification sound under one second.”** Read tools include `search_sounds`, `get_sound`, `list_categories` and `get_prompt_template`. The skill can fall back to public catalog pages when MCP is unavailable.

This skill focuses on finding and using sounds. Publication is a separate workflow; MCP submission is not included in the verified setup.

## Run locally

Requires **Node.js 22.18 or newer**. The repo includes an `.nvmrc`.

```bash
git clone https://github.com/Tguntenaar/opus-sound-directory.git
cd opus-sound-directory
npm install
npm run dev
```

Open **[localhost:43123](http://127.0.0.1:43123)**.

| I want to… | Go here |
| :--- | :--- |
| Generate or add a sound | [Adding an entry](docs/DEVELOPMENT.md#adding-an-entry) |
| Understand the audio pipeline | [Runner guide](docs/DEVELOPMENT.md#runner-runner) |
| Build or deploy the site | [Development and operations](docs/DEVELOPMENT.md) |
| Review community submissions | [Review workflow](docs/DEVELOPMENT.md#reviewing-submissions) |
| Read the sound-generation history | [Provenance](provenance/README.md) |

## Contribute

Have a sound idea, a better synthesis approach or a fix? [Open an issue](https://github.com/Tguntenaar/opus-sound-directory/issues/new), [submit a sound](https://opussounds.directory/submit), or send a pull request.

Read the [contribution guide](CONTRIBUTING.md) for audio requirements, attribution and licensing. If the directory helps your work, a GitHub star helps others find it.

## License

**Everyone can use this project, including for commercial work.**

| Material | License | What that means |
| :--- | :--- | :--- |
| Audio, spectrograms and sound prompts, including masters and archived candidate takes | [CC0 1.0](ASSETS-LICENSE.md) | Copy, edit, remix, redistribute and use commercially without asking permission or giving credit. |
| Application code, synthesis scripts, configuration, tooling and documentation | [MIT](LICENSE) | Use, modify, distribute and sell; retain the copyright and license notice in copies or substantial portions. |

See the [asset scope](ASSETS-LICENSE.md), [full CC0 text](LICENSES/CC0-1.0.txt) and [MIT license](LICENSE). Third-party dependencies retain their own licenses. CC0 does not grant trademark or endorsement rights.

---

<div align="center">

**A sound directory you can listen to, learn from and build on.**

[Browse sounds](https://opussounds.directory) · [Contribute](CONTRIBUTING.md) · [Back to top](#opus-sounds-directory)

</div>
