# Understanding how visitors use Opus Sounds

The directory uses PostHog to measure discovery, listening, reuse, and contributions. Explicit events distinguish clicking a button from finishing the action, so a busy page does not automatically look like a successful experience.

## Read usage reports

Run `node scripts/analytics-report.mjs --queries` to print ready-to-use SQL queries for the PostHog SQL editor. The queries default to the last 30 days; set `ANALYTICS_DAYS` to an integer from 1 to 365 to change the window.

To fetch the reports locally, supply `POSTHOG_PERSONAL_API_KEY` and `POSTHOG_PROJECT_ID` through your environment and run `node scripts/analytics-report.mjs`. The personal key needs access to this project and `query:read`. `POSTHOG_API_HOST` defaults to `https://us.posthog.com`; EU projects use `https://eu.posthog.com`. Never put a personal key into a public frontend variable. See [PostHog API authentication](https://posthog.com/docs/api).

The JSON output contains event totals and distinct anonymous browser counts, sign-ins by provider, contribution steps, sound popularity, unsuccessful searches, errors, and discovery choices. A browser count is not a count of known people: one person may use multiple devices, and blocked analytics is not observed. The report reads data; it does not create a hosted dashboard.

## Events and questions

| Question | Events and breakdowns |
| --- | --- |
| How many visitors click Add your sound? | `add_sound_click`, split by `placement` (home_hero, footer, account). Compare total clicks and unique visitors. |
| Do visitors choose Google or GitHub? | `auth_sign_in_clicked`, `auth_sign_in_started`, `auth_sign_in_succeeded`, `auth_sign_in_failed`, split by `provider` and `source`. |
| Where do contributors stop? | `submit_agent_token_click`, `submit_agent_setup_click`, `submit_manual_open`, `submit_form_access`, `submit_form_start`, `submit_form_attempt`, `submit_form_validation_error`, `submit_form_error`, `submit_form_submit`, `submit_status_live`. |
| Which sounds attract and retain interest? | `sound_impression`, `sound_detail_click`, `sound_play`, `sound_progress`, `sound_complete`, `sound_play_error`, grouped by `sound_id` and `source`. |
| Which sounds do visitors reuse? | `sound_download`, `sound_copy_prompt`, `sound_copy_code`, `sound_share`. Downloads measure link clicks, not completed file transfers. |
| What is missing or hard to find? | `search` with `result_count = 0`, `filter_change`, and `sort_change`. |

Create a PostHog funnel from `auth_sign_in_clicked` → `auth_sign_in_started` → `auth_sign_in_succeeded`, using a one-hour conversion window and a provider breakdown. For manual contributions, use `submit_manual_open` → `submit_form_start` → `submit_form_attempt` → `submit_form_submit`. Compare unique visitors within the same date range. The report's individual step counts are diagnostic totals, not an ordered funnel or conversion rate.

OAuth success means the visitor returned to the site and an account session was confirmed. Closing the provider tab appears as drop-off. Attribution requires browser session storage and expires after one hour. New explicit events cannot reconstruct historical clicks or sign-in attempts. New submission events send field identifiers and status classifications, never form drafts, source code, names, or token values.

## Popular ordering

New visitors see Popular. An explicit Popular/Newest preference is saved in the browser. Popularity uses `plays + 3 × copies + 5 × download clicks`; ties use the newer sound. Reuse receives more weight than listening. Catalog and community sounds participate. A play is counted after the audio actually begins; the public counter counts each sound once per mounted browsing session. Detailed PostHog play events can include replays.

Ranking is held steady while browsing so sounds do not move under the pointer during playback. Public counters are approximate: Cloudflare KV read/modify/write increments can lose concurrent updates, clients can block or repeat requests, and counters are not unique-person counts. Use PostHog reports for date-window comparisons. Low counts are not strong evidence of preference.

## Decide what to improve

- Many sign-in clicks but few starts: inspect start-stage errors and provider configuration.
- Starts without returns: compare providers and check callback failures before changing the sign-in screen.
- Manual opens without form starts: assess sign-in access and the effort required to contribute.
- Attempts without accepted submissions: inspect validation fields and server error status counts.
- Frequent zero-result searches: consider new sounds, tags, or search matching for those terms.
- Many listens but few copies/downloads: compare sound quality, use cases, and the visibility of reuse controls.
- Many impressions but few listens: review titles and categories; compare within similar positions and sources to limit ranking bias.

Verify production events in PostHog after deploying with the public project key configured. Do Not Track and blockers may prevent collection. Local browser tests use a test project key and mocked account/submission responses.
