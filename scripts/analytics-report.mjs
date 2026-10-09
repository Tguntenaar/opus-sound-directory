/** Read-only PostHog usage report. Credentials stay in the local environment. */
import { pathToFileURL } from 'node:url';

export function buildQueries(days = 30) {
  if (!Number.isInteger(days) || days < 1 || days > 365) throw new Error('Days must be an integer from 1 to 365.');
  const period = `timestamp >= now() - INTERVAL ${days} DAY`;
  const counts = 'count() AS events, uniq(distinct_id) AS visitors';
  return {
    overview: `SELECT event, ${counts} FROM events WHERE ${period} AND event IN ('$pageview', 'add_sound_click', 'auth_sign_in_clicked', 'auth_sign_in_started', 'auth_sign_in_succeeded', 'auth_sign_in_failed', 'submit_form_start', 'submit_form_attempt', 'submit_form_submit', 'submit_form_error', 'sound_play', 'sound_complete', 'sound_download', 'sound_copy_prompt', 'sound_copy_code', 'sound_share') GROUP BY event ORDER BY events DESC`,
    sign_in: `SELECT event, properties.provider AS provider, properties.source AS source, ${counts} FROM events WHERE ${period} AND event LIKE 'auth_sign_in_%' GROUP BY event, provider, source ORDER BY provider, event`,
    contribution: `SELECT event, properties.placement AS placement, ${counts} FROM events WHERE ${period} AND (event = 'add_sound_click' OR event LIKE 'submit_%') GROUP BY event, placement ORDER BY events DESC`,
    popular_sounds: `SELECT properties.sound_id AS sound_id, uniqIf(distinct_id, event = 'sound_play') AS listeners, countIf(event = 'sound_play') AS plays, countIf(event = 'sound_complete') AS completions, countIf(event = 'sound_download') AS download_clicks, countIf(event IN ('sound_copy_prompt', 'sound_copy_code')) AS copies, countIf(event = 'sound_share') AS shares FROM events WHERE ${period} AND event IN ('sound_play', 'sound_complete', 'sound_download', 'sound_copy_prompt', 'sound_copy_code', 'sound_share') GROUP BY sound_id ORDER BY download_clicks DESC, listeners DESC, copies DESC LIMIT 50`,
    search_gaps: `SELECT properties.query AS query, ${counts} FROM events WHERE ${period} AND event = 'search' AND properties.result_count = 0 GROUP BY query ORDER BY events DESC LIMIT 30`,
    failures: `SELECT event, properties.stage AS stage, coalesce(properties.reason, properties.failure_reason) AS reason, ${counts} FROM events WHERE ${period} AND (event LIKE 'auth_sign_in_failed' OR event LIKE 'submit_%error' OR event LIKE 'submit_%failed' OR event = 'sound_play_error') GROUP BY event, stage, reason ORDER BY events DESC`,
    discovery: `SELECT event, properties.filter AS filter, properties.value AS value, properties.sort AS sort, ${counts} FROM events WHERE ${period} AND event IN ('filter_change', 'sort_change') GROUP BY event, filter, value, sort ORDER BY events DESC`,
  };
}

async function main() {
  const days = Number(process.env.ANALYTICS_DAYS || 30);
  const queries = buildQueries(days);
  if (process.argv.includes('--queries')) {
    console.log(JSON.stringify(queries, null, 2));
    return;
  }
  const key = process.env.POSTHOG_PERSONAL_API_KEY;
  const project = process.env.POSTHOG_PROJECT_ID;
  if (!key || !project || !/^\d+$/.test(project)) {
    throw new Error('Set POSTHOG_PERSONAL_API_KEY and numeric POSTHOG_PROJECT_ID. Use --queries to print SQL without credentials.');
  }
  const host = new URL(process.env.POSTHOG_API_HOST || 'https://us.posthog.com');
  if (host.protocol !== 'https:' || host.username || host.password) throw new Error('POSTHOG_API_HOST must be an HTTPS app host.');
  const report = { days, generated_at: new Date().toISOString(), reports: {} };
  for (const [name, query] of Object.entries(queries)) {
    const response = await fetch(new URL(`/api/projects/${project}/query/`, host), {
      method: 'POST',
      headers: { Authorization: `Bearer ${key}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: { kind: 'HogQLQuery', query } }),
      signal: AbortSignal.timeout(60_000),
    });
    if (!response.ok) throw new Error(`PostHog ${name} query returned HTTP ${response.status}. Check project access and query:read permission.`);
    const result = await response.json();
    if (!Array.isArray(result.results)) throw new Error(`PostHog ${name} query did not return completed results. Retry in PostHog.`);
    report.reports[name] = { columns: result.columns, rows: result.results };
  }
  console.log(JSON.stringify(report, null, 2));
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => { console.error(error.message); process.exitCode = 1; });
}
