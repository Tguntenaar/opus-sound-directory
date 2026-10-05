# Opus Sound Directory

Browsable directory of **Claude Opus–generated** synthesised audio: prompts, Python code, waveforms, spectrograms, and loudness metrics. Inspired by the *idea* of a plugin directory, not any third-party implementation.

## Concept

Each **entry** is a JSON file in `content/entries/` plus assets under `public/assets/<id>/`. The site shows:

- Prompt (with copy button)
- Audio player
- Generated Python
- Spectrogram
- LUFS / true peak / length
- Model ID and run date

Audio is **synthesised** (numpy/scipy) for precise, royalty-free, video-timed beds and SFX — not realistic instruments or vocals. Use your ears for final taste.

## Quick start (site)

Requires **Node.js ≥ 22.18** (Cloudflare vite plugin). Use `.nvmrc` if you use nvm.

```bash
npm install
npm run dev
```

Open [http://127.0.0.1:43123](http://127.0.0.1:43123).

```bash
npm run build    # production build (vinext + Cloudflare)
npm run start    # preview production build locally
npm run deploy   # build + deploy via vinext-cloudflare → cf deploy
```

### Deploy to Cloudflare Workers

Worker name: **`opus-sound-directory`** (`cloudflare.config.ts`). With no custom domain, Cloudflare serves **`https://opus-sound-directory.<your-subdomain>.workers.dev`**.

**Authenticate (pick one):**

1. **API token (recommended for CI / Cloud Agents)**  
   - Create a token at [Cloudflare API tokens](https://dash.cloudflare.com/profile/api-tokens) (e.g. **Edit Cloudflare Workers** template).  
   - Export before deploy:
     ```bash
     export CLOUDFLARE_API_TOKEN="your-token"
     # If you have multiple accounts:
     export CLOUDFLARE_ACCOUNT_ID="your-account-id"
     ```
   - In Cursor Cloud Agent, add the same vars as environment secrets, then re-run deploy.

2. **OAuth (local machine)**  
   ```bash
   npx cf auth login
   npx cf auth whoami   # should show authenticated: true
   npm run deploy
   ```

Requires Node ≥ 22.18 (`nvm use` / `.nvmrc`).

### Temporary preview deploy (no API token)

Wrangler 4.102+ can provision a **60-minute temporary account** (claim in dashboard):

```bash
npm run build
CI=true npx wrangler deploy --temporary --config wrangler.temporary.jsonc
```

Workers static assets are limited to **5 MiB per file**; long beds may need R2 or re-encoded WAVs for Workers-only hosting.

Stack: **Next.js via [vinext](https://github.com/nicolo-ribaudo/vinext)** on Cloudflare Workers, Tailwind CSS.

### Cloudflare / R2 (later)

- Today: static WAV/MP3/spectrograms live in `public/assets/` and ship with the Worker.
- **R2**: move large assets to a bucket, set `assets.wav` URLs in entry JSON to public R2 URLs, and optionally add a Worker route for signed URLs. No code changes required to the JSON schema.

## Adding an entry

1. Copy an existing file in `content/entries/*.json` and edit `id`, `slug`, `title`, `category`, `prompt`, `timing`, and `cues`.
2. Run the runner (mock mode fills assets and metrics):

   ```bash
   pip install -r runner/requirements.txt
   python3 runner/run.py content/entries/your-id.json --mock
   ```

3. Commit the JSON and `public/assets/your-id/` files.

Day-one seed (16 entries):

```bash
python3 runner/seed_day_one.py
```

### Entry categories

`chaos-calm`, `ad-beds`, `drops`, `risers`, `ui-sounds`, `logo-stings`, `ambient`

## Runner (`runner/`)

| Script | Purpose |
|--------|---------|
| `run.py` | Generate + verify one entry |
| `seed_day_one.py` | Create 16 MVP entries and assets |
| `mock_generate.py` | Placeholder synthesis when no Claude API |
| `verify.py` | Length, LUFS/peak (ffmpeg `ebur128` if installed), spectrogram |
| `lib/audio_lib.py` | Shared drums/synth/reverb/limiter API sketch |

### CLI

```bash
python3 runner/run.py content/entries/chaos-calm-01.json --mock
python3 runner/run.py content/entries/chaos-calm-01.json --mock --best-of 3
```

- **`--mock`** (default): numpy placeholder WAV, updates `metrics` in JSON.
- **`--agent`**: reserved for real generation (not wired in MVP). To integrate later:
  - **Claude Code CLI**: `claude -p "$(cat prompt.txt)"` with a project rule to write `generate.py` and run verification.
  - **Agent SDK**: implement `agent_generate()` in `run.py` to call your agent with the entry prompt + seed, then run the same `verify.py` pipeline.

### Verification

Uses `ffmpeg -af ebur128` when `ffmpeg` is on PATH; otherwise estimates LUFS/peak in Python. Spectrograms via matplotlib.

## License

New project code in this repo; no code copied from `cursor/community-plugins`.
