# PostHog analytics (Opus Sounds Directory)

Product analytics use [PostHog](https://posthog.com) US cloud. Events are **snake_case**. When `NEXT_PUBLIC_POSTHOG_KEY` is unset at build time, the browser SDK never initializes and server capture no-ops.

## Environment variables

| Variable | Where | Purpose |
|----------|--------|---------|
| `NEXT_PUBLIC_POSTHOG_KEY` | Build-time (CI / local) | Public project API key (`phc_…`). Required for client analytics. |
| `NEXT_PUBLIC_POSTHOG_HOST` | Build-time (optional) | API host for proxy upstream (default `https://us.i.posthog.com`). |
| `POSTHOG_KEY` | Worker secret / var (optional) | Server-side capture (`/capture`). Falls back to inlined `NEXT_PUBLIC_POSTHOG_KEY` if set at build. |

Client SDK uses first-party **`/api/ingest`** (`api_host`) so event POSTs are not broken by vinext trailing-slash **308** redirects (only `/api/*` is exempt). Legacy **`/ingest`** is still proxied. UI links use `https://us.posthog.com`.

## Event catalog

### Sound engagement

| Event | Properties |
|-------|------------|
| `sound_play` | `sound_id`, `category`, `mood`, `model_id`, `source` |
| `sound_complete` | same |
| `sound_seek` | same + `position_ratio` |
| `sound_copy_prompt` | same |
| `sound_copy_code` | same |
| `sound_download` | same + `format` (`wav` \| `mp3`) |
| `sound_share` | same |

`source`: `card` \| `detail` \| `featured` \| `blog_embed`

KV copy/download counters are unchanged; these events are additive.

### Browse

| Event | Properties |
|-------|------------|
| `search` | `query`, `result_count` (debounced ~450ms, min 2 chars) |
| `filter_change` | `filter` (`category` \| `mood`), `value` |
| `sort_change` | `sort` (`popular` \| `new`) |

### Sponsor & submit

| Event | Properties | Notes |
|-------|------------|--------|
| `sponsor_cta_click` | `placement` (`featured_slot` \| `blog` \| `blog-index`), `slug` (post slug when `placement=blog`), `sponsored` | Blog card / index CTAs |
| `sponsor_form_submit` | `package_count`, `budget_range`, optional `ref` | No email or company name; `ref` from `?ref=` on `/sponsor` |
| `submit_form_submit` | `submission_id`, `source`, `category`, `mood_count` | No email or code |
| `submit_status_live` | `submission_id`, `community_slug` (server), `source` | When a submission goes live |

### MCP & blog

| Event | Properties |
|-------|------------|
| `mcp_tool_call` | `tool`, `ok`, `latency_ms` |
| `blog_related_guide_click` | `category`, `guide_slug` |

### Outbound

| Event | Properties |
|-------|------------|
| `outbound_click` | `destination` (`github` \| `x` \| `profile`), `href` |

PostHog autocapture also records UTM parameters and referrer when present; the ingest proxy forwards request headers.

## Suggested PostHog insights

### 1. Top sounds by plays

1. **Insights → New insight → Trends**
2. Event: `sound_play`
3. Breakdown: `sound_id`
4. Chart: bar or table, last 30 days

### 2. Download conversion by category

1. **Insights → New insight → Funnels**
2. Step 1: `sound_play` (filter or breakdown `category` on step 2)
3. Step 2: `sound_download`
4. Breakdown: `category`
5. Optional: add filter `format` = `wav` or `mp3`

### 3. Traffic sources

1. **Insights → New insight → Trends**
2. Event: `$pageview` (or `sound_play` for engaged traffic)
3. Breakdown: `$referring_domain` or UTM properties (`utm_source`, `utm_medium`, `utm_campaign`)

Session recording is not enabled in code; turn it on from the PostHog project settings when you want it (remote config via `/decide`).
