# Development and operations

[← Back to the directory](../README.md)

## Quick start (site)

Requires **Node.js ≥ 22.18** (Cloudflare vite plugin). Use `.nvmrc` if you use nvm.

```bash
npm install
npm run dev
```

Open [http://127.0.0.1:43123](http://127.0.0.1:43123).

### Blog

Posts live in `content/blog/<slug>.md` with YAML frontmatter (`title`, `slug`, `description`, `date`, `keywords[]`, `faq`, optional `draft: true`). `npm run prebuild` runs `scripts/sync-blog.mjs` to regenerate `lib/blog.generated.ts`. Published posts appear at `/blog`, in `/sitemap.xml`, `/blog/rss.xml`, and `/llms.txt`. Set `draft: true` to keep a post out of listings, RSS, sitemap, and LLM indexes.

Embed a sound on its own line in markdown:

```md
[Success chime](/e/ui-success-chime)
```

```bash
npm run build    # production build (vinext + Cloudflare)
npm run start    # preview production build locally
npm run deploy   # build + deploy via vinext-cloudflare → cf deploy
```

### IndexNow (after deploy)

Verification file: `https://opussounds.directory/opus-sounds-directory-indexnow-key-2026.txt` (override with `INDEXNOW_KEY`).

```bash
SITE_URL=https://opussounds.directory node scripts/indexnow.mjs
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

Workers static assets are limited to **5 MiB per file**. By default, WAV downloads use the static asset at `/audio/<entry-id>/out.wav` (downsampled copy under `public/assets/<id>/out.wav` when needed). After R2 is enabled on the account, swap deploy config to serve full **48 kHz** masters from bucket `opus-sounds-audio`:

```bash
cp cloudflare.config.with-r2.ts cloudflare.config.ts && npm run deploy
```

Uncomment the `r2_buckets` block in `wrangler.temporary.jsonc` for temporary preview deploys with R2.

**48 kHz masters (not deployed as static assets)** live in `masters/<entry-id>/out.wav`. The runner copies each mastered WAV there before optional downsampling for Workers.

After deploy, create the R2 bucket if needed (dashboard → **R2** → create `opus-sounds-audio`), then upload masters:

```bash
node scripts/upload-wavs-r2.mjs
```

That runs `wrangler r2 object put opus-sounds-audio/<entry-id>/out.wav --file=masters/<entry-id>/out.wav --content-type=audio/wav --remote` for every entry. Requires `CLOUDFLARE_API_TOKEN` or `wrangler login`.

Stack: **Next.js via [vinext](https://github.com/nicolo-ribaudo/vinext)** on Cloudflare Workers, Tailwind CSS.

### SEO, sharing, and crawl

- **Open Graph / Twitter** — `app/layout.tsx` + `lib/site-metadata.ts` (default image `public/og-default.png`, 1200×630). Entry pages use each asset’s **spectrogram** as `og:image` via `generateMetadata` in `app/e/[slug]/page.tsx`.
- **`/sitemap.xml`** — `app/sitemap.ts` (home, `/sponsor`, all `/e/[slug]`).
- **`/robots.txt`** — `app/robots.ts` (allow all, `Sitemap:` absolute URL).

Set the public origin before build/deploy so canonical and social URLs are correct:

```bash
export SITE_URL="https://opus-sound-directory.<your-subdomain>.workers.dev"
# Production: SITE_URL="https://opussounds.directory"
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

- **POST `/api/sponsor`** — JSON body with company/contact/email/website/packages/budget/message (optional `logoUrl`). Returns `{ ok: true, id }` (`id` is the lead id for tracing; honeypot replies stay `{ ok: true }`). Honeypot field `companyFax` must stay empty.
- **GET `/api/sponsor`** — disabled (`{ enabled: false, leads: [] }`) until you set Worker secret **`SPONSOR_ADMIN_TOKEN`**. Then pass `Authorization: Bearer <token>` or header `X-Sponsor-Admin-Token` to list recent leads.

**KV namespace (`SPONSOR_KV`):** On first deploy, `bindings.kv()` in `cloudflare.config.ts` usually provisions a namespace per binding name. If deploy fails, create one in the dashboard (**Workers KV** → **Create**), then pin it:

```ts
SPONSOR_KV: bindings.kv({ id: "<namespace-id>" }),
```

(`STATS_KV` is separate — sponsor data does not share the stats namespace.)

**Optional email alert** after each lead (MVP works without it):

1. Enable [Email Sending](https://developers.cloudflare.com/email-service/) on your domain (`wrangler email sending enable yourdomain.com`).
2. `cloudflare.config.ts` already declares **`SPONSOR_SEND_EMAIL`** (`bindings.sendEmail()`).
3. Set Worker variable **`SPONSOR_MAIL_FROM`** to a verified sender on that domain (e.g. `sponsors@yourdomain.com`). Optional **`SPONSOR_MAIL_TO`** is a comma/semicolon list (default `olivierguntenaar@gmail.com,thomas@guntenaar.org`). Optional Worker secrets **`SPONSOR_NOTIFY_WEBHOOK_URL`** and **`SPONSOR_NOTIFY_WEBHOOK_KEY`** POST the lead JSON after email (or skip).

```bash
curl -s -H "Authorization: Bearer $SPONSOR_ADMIN_TOKEN" https://your-worker.example/api/sponsor | jq
```

### Cloudflare / R2 (later)

- Today: static WAV/MP3/spectrograms live in `public/assets/` and ship with the Worker.
- **R2**: move large assets to a bucket, set `assets.wav` URLs in entry JSON to public R2 URLs, and optionally add a Worker route for signed URLs. No code changes required to the JSON schema.

## Adding an entry

**Pending sound candidates:** [Codex Hero8 collection](../provenance/codex-generations/README.md) contains 27 takes for nine sounds, with an offline listening page and measured QA. These await listening selection and are not part of the live catalog.

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

Metrics in the JSON are measured from the shipped file (`verify.py` + ffmpeg `ebur128` when available). Beds longer than ~30 s at 48 kHz stereo may be auto-downsampled (32 kHz, 24 kHz, 22.05 kHz, or 16 kHz **stereo**) to stay under the Workers **5 MiB** per-file limit (`runner/ship_wav.py`); MP3 is encoded from the full-rate master before downsampling. `timing.sampleRate` / `timing.samples` in JSON match the shipped WAV.

| Script | Purpose |
|--------|---------|
| `run.py` | Synthesise, verify, update JSON metrics, export `generate.py`, stamp `modelId` / mood |
| `entry_meta.py` | Per-entry `mood` / `tempo`; `local-synth` + `targetModelId` (`claude-opus-5-5`) |
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

- **`--mock`** (default): runs the per-entry numpy synthesiser, sets **`modelId`: `local-synth`** (honest — not an API call), **`targetModelId`: `claude-opus-5-5`**, mood/tempo from `entry_meta.py`, and updates `metrics` in JSON.
- **`--pipeline-only`**: skip synthesis; remaster `out.wav` (pyloudnorm LUFS + peak limit), ffmpeg verify, spectrogram, MP3, Workers sizing. Use after dropping in Opus `generate.py` / WAV. Add **`--run-generate-py`** to execute the asset script first. **`--preserve-model-id`** keeps `modelId: claude-opus-5-5` (no `targetModelId`).
- **`--agent`**: reserved for real generation (not wired in MVP). To integrate later:
  - **Claude Code CLI**: `claude -p "$(cat prompt.txt)"` with a project rule to write `generate.py` and run verification.
  - **Agent SDK**: implement `agent_generate()` in `run.py` to call your agent with the entry prompt + seed, then run the same `verify.py` pipeline.

### Verification

Uses `ffmpeg -af ebur128` when `ffmpeg` is on PATH; otherwise estimates LUFS/peak in Python. Spectrograms via matplotlib.

### Remote MCP server (`/mcp`)

Public **Model Context Protocol** endpoint (streamable HTTP, stateless) for LLM clients:

- **URL:** `https://opussounds.directory/mcp` (also in repo root `.mcp.json` for cursor.directory auto-scan)
- **Browser info:** `GET /mcp` with `Accept: text/html` shows install snippets
- **Tools:** `search_sounds`, `get_sound`, `list_categories`, `get_prompt_template`, `submit_sound`, `get_submission_status`
- **Resources (optional):** `opus://sound/<id>` for static catalog entries

**Cursor** — add to `.mcp.json`:

```json
{ "mcpServers": { "opus-sounds": { "url": "https://opussounds.directory/mcp" } } }
```

**Claude Code / Desktop:**

```bash
claude mcp add --transport http opus-sounds https://opussounds.directory/mcp
```

Read tools need no auth. `submit_sound` requires an account-issued token in the `Authorization: Bearer …` header. It creates a submission owned by the authenticated account. The web form uses a signed session cookie; typed email addresses cannot override ownership. `get_submission_status` and the web status endpoint return only the caller's own submissions. Legacy anonymous submissions remain available to administrators but cannot be claimed by typing the same email.

See [account setup](ACCOUNTS.md) for GitHub/Google OAuth, D1 migrations, and token configuration.

### Reviewing submissions

Web (`POST /api/submit`) and MCP (`submit_sound`) share one review pipeline:

1. Sign-in, verified email, and a per-account cooldown are required. New submissions are stored in D1; existing KV submissions remain readable by administrators.
2. Static checks flag suspicious code, claims, and spam. These checks do not make Python safe to execute.
3. Workers AI reviews the entire supported code input and returns structured quality and rights concerns. Missing AI, malformed output, or code beyond the review limit requires human review.
4. Flagged or rejected submissions remain unpublished, with an email warning attempt recorded. Text review alone does not certify audio or establish legal clearance.

**Automatic Python rendering and audio hosting are not enabled in this change.** Even a passing text/code review remains `pending_review` until audio generation, validation, and hosting are connected. Administrator approval remains available. Never execute contributed Python inside the website Worker or an unrestricted host process.

Status values: `scanning` → `live` | `pending_review` | `rejected`. Signed-in contributors can follow their recent submissions at `/account`.

Warnings use the existing Email Sending binding with private `SUBMIT_MAIL_TO` and `SUBMIT_MAIL_FROM` settings (the latter can fall back to `SPONSOR_MAIL_FROM`). Use a verified destination address for free destination-restricted sending. Configure and verify a sending domain first. The review dashboard shows whether sending was accepted, failed, or was unconfigured. Delivery currently has no durable automatic retry; administrators must check failed warnings in the dashboard.

**Admin overrides** — `/admin/review` + `GET/POST /api/admin/review` protected by Worker secret **`REVIEW_ADMIN_TOKEN`** (Bearer, `?token=`, or `X-Review-Admin-Token`). Approve publishes from queue; unpublish removes a community KV entry. Curated git entries still ship via `runner/run.py` and a normal PR.

**Secrets to set (production):**

```bash
npx wrangler secret put REVIEW_ADMIN_TOKEN
# optional, existing:
npx wrangler secret put SPONSOR_ADMIN_TOKEN
```

Enable Workers AI on the account; the `AI` binding is declared in `cloudflare.config.ts`.

## License

- **Code** (site, runner, tooling): [MIT License](../LICENSE) — Copyright (c) 2026 Thomas Guntenaar
- **Sounds** (audio and spectrograms under `public/assets/`, plus entry prompt text in `content/entries/`): [CC0 1.0 Universal](../ASSETS-LICENSE.md)

Community submissions via the form or pull requests are accepted under the same terms (code MIT, audio and prompts CC0). No code was copied from `cursor/community-plugins`.
