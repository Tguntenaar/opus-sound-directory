# Opus Sound Directory

Browsable directory of **Claude Opus–generated** synthesised audio: prompts, Python code, waveforms, spectrograms, and loudness metrics. Inspired by the *idea* of a plugin directory, not any third-party implementation.

## Concept

Each **entry** is a JSON file in `content/entries/` plus assets under `public/assets/<id>/`. The site shows:

- Prompt (with copy button)
- Audio player
- Generated Python
- Spectrogram
- LUFS / true peak / length
- **Mood / tempo** chips (`mood[]`, optional `tempo`)
- **Model attribution** (`modelId` — today `local-synth` for numpy runner; `targetModelId` for planned Opus agent runs)
- Run date

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

### SEO, sharing, and crawl

- **Open Graph / Twitter** — `app/layout.tsx` + `lib/site-metadata.ts` (default image `public/og-default.png`, 1200×630). Entry pages use each asset’s **spectrogram** as `og:image` via `generateMetadata` in `app/e/[slug]/page.tsx`.
- **`/sitemap.xml`** — `app/sitemap.ts` (home, `/sponsor`, all `/e/[slug]`).
- **`/robots.txt`** — `app/robots.ts` (allow all, `Sitemap:` absolute URL).

Set the public origin before build/deploy so canonical and social URLs are correct:

```bash
export SITE_URL="https://opus-sound-directory.<your-subdomain>.workers.dev"
# After custom domain: SITE_URL="https://opussound.directory"
npm run build && npm run deploy
```

Regenerate the default share image after branding changes: `python3 scripts/generate-og-default.py`.

### Cloudflare Web Analytics (optional, dashboard only)

No beacon is wired in this repo. To enable: Cloudflare dashboard → **Workers & Pages** → your Worker → **Metrics** / **Web Analytics** (or zone **Analytics** → **Web Analytics** when using a custom domain). No code change required for basic page views.

### Copy / download stats (Workers KV)

Prompt copies and audio downloads are counted per entry via **`STATS_KV`** in `cloudflare.config.ts`.

- **API:** `GET /api/stats` returns all entry counts; `POST /api/stats` with `{ "id": "<entry-id>", "event": "copy" | "download" }` increments.
- **Keys:** `stats:<entry-id>:copy` and `stats:<entry-id>:download` (integers as strings).
- **UI:** optimistic updates on copy, download links, and browse cards.

**Dashboard setup (first permanent deploy):**

1. Deploy with `npm run deploy` (or `cf deploy --prebuilt`). The `bindings.kv()` entry usually **creates** a KV namespace named for the binding (`STATS_KV`) on first upload.
2. In [Cloudflare Dashboard](https://dash.cloudflare.com) → **Workers & Pages** → your Worker → **Bindings**, confirm **KV namespace** `STATS_KV` is attached.
3. If deploy errors on KV, create a namespace manually (**Workers KV** → **Create**), copy its ID, and set `STATS_KV: bindings.kv({ id: "…" })` in `cloudflare.config.ts`.

Local `npm run dev` uses an in-memory fallback when KV is unavailable; production needs the binding.

### Sponsor leads (`/sponsor`)

Public interest form at **`/sponsor`** (header/footer **Sponsors**). Leads are stored in **`SPONSOR_KV`** (`sponsor:lead:{uuid}` plus index key `sponsor:index`).

- **POST `/api/sponsor`** — JSON body with company/contact/email/website/packages/budget/message (optional `logoUrl`). Returns `{ ok: true }`. Honeypot field `companyFax` must stay empty.
- **GET `/api/sponsor`** — disabled (`{ enabled: false, leads: [] }`) until you set Worker secret **`SPONSOR_ADMIN_TOKEN`**. Then pass `Authorization: Bearer <token>` or header `X-Sponsor-Admin-Token` to list recent leads.

**KV namespace (`SPONSOR_KV`):** On first deploy, `bindings.kv()` in `cloudflare.config.ts` usually provisions a namespace per binding name. If deploy fails, create one in the dashboard (**Workers KV** → **Create**), then pin it:

```ts
SPONSOR_KV: bindings.kv({ id: "<namespace-id>" }),
```

(`STATS_KV` is separate — sponsor data does not share the stats namespace.)

**Optional email alert** after each lead (MVP works without it):

1. Enable [Email Sending](https://developers.cloudflare.com/email-service/) on your domain (`wrangler email sending enable yourdomain.com`).
2. `cloudflare.config.ts` already declares **`SPONSOR_SEND_EMAIL`** (`bindings.sendEmail()`).
3. Set Worker variable **`SPONSOR_MAIL_FROM`** to a verified sender on that domain (e.g. `sponsors@yourdomain.com`). Optional **`SPONSOR_MAIL_TO`** overrides the default `thomas@guntenaar.org`.

```bash
curl -s -H "Authorization: Bearer $SPONSOR_ADMIN_TOKEN" https://your-worker.example/api/sponsor | jq
```

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

Each entry has a **distinct** synthesiser in `runner/synth/entry_synth.py`. The runner writes:

- `public/assets/<id>/out.wav` (+ `out.mp3` when ffmpeg is installed)
- `public/assets/<id>/spectrogram.png`
- `public/assets/<id>/generate.py` — **executable** code that reproduces the WAV (embeds `runner/templates/synth_runtime.py` + entry function)

Metrics in the JSON are measured from the shipped file (`verify.py` + ffmpeg `ebur128` when available). Beds longer than ~30 s at 48 kHz stereo may be auto-downsampled to **32 kHz mono** to stay under the Workers **5 MiB** per-file limit (`runner/ship_wav.py`); `timing.sampleRate` / `timing.samples` in JSON match the shipped WAV.

| Script | Purpose |
|--------|---------|
| `run.py` | Synthesise, verify, update JSON metrics, export `generate.py`, stamp `modelId` / mood |
| `entry_meta.py` | Per-entry `mood` / `tempo`; `local-synth` + `targetModelId` (`claude-opus-4-20250514`) |
| `synth/entry_synth.py` | Per-entry sound design (16 ids) |
| `verify.py` | Length, LUFS/peak, spectrogram |
| `code_writer.py` | Export self-contained `generate.py` |
| `ship_wav.py` | Optional downsample for Workers asset limits |

### CLI

```bash
pip install -r runner/requirements.txt   # numpy, matplotlib; ffmpeg optional but recommended

# One entry
python3 runner/run.py content/entries/chaos-calm-01.json

# All 16
for f in content/entries/*.json; do python3 runner/run.py "$f"; done

# Re-render from published code only
python3 public/assets/chaos-calm-01/generate.py
```

```bash
python3 runner/run.py content/entries/chaos-calm-01.json --mock
python3 runner/run.py content/entries/chaos-calm-01.json --mock --best-of 3
```

- **`--mock`** (default): runs the per-entry numpy synthesiser, sets **`modelId`: `local-synth`** (honest — not an API call), **`targetModelId`: `claude-opus-4-20250514`**, mood/tempo from `entry_meta.py`, and updates `metrics` in JSON.
- **`--agent`**: reserved for real generation (not wired in MVP). To integrate later:
  - **Claude Code CLI**: `claude -p "$(cat prompt.txt)"` with a project rule to write `generate.py` and run verification.
  - **Agent SDK**: implement `agent_generate()` in `run.py` to call your agent with the entry prompt + seed, then run the same `verify.py` pipeline.

### Verification

Uses `ffmpeg -af ebur128` when `ffmpeg` is on PATH; otherwise estimates LUFS/peak in Python. Spectrograms via matplotlib.

## License

New project code in this repo; no code copied from `cursor/community-plugins`.
