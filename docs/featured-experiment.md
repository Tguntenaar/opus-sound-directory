# Homepage featured sound

The editorial default is **Endless riser (Shepard + Risset)**. Sponsored placements take precedence and do not enter the experiment.

## PostHog setup

Create an experiment using the multivariate flag `homepage-featured-sound-v1`:

| Variant | Allocation | Sound |
| --- | --- | --- |
| `control` | 50% | Chaos clocks → calm (`chaos-calm-01`) |
| `endless-riser` | 50% | Endless riser (`endless-riser-shepard`) |

Use the custom exposure event `featured_sound_exposure`, filtered by `experiment = homepage-featured-sound-v1`. Its `$feature/homepage-featured-sound-v1` property identifies the variant. The event is emitted when at least half the card is visible in an active tab, once per browser session where session storage is available. Do not use automatic flag evaluation as exposure: flag reads deliberately suppress that event.

Choose average session duration as the primary outcome. Compare completed sessions only, with one observation per exposed session, rather than weighting visitors by their number of pageviews. Duration is PostHog's measured session span, not focused reading time. Existing `sound_play`, `sound_download`, and `sound_copy_prompt` events are useful secondary outcomes. Use the same exposure cohort for both variants and inspect uncertainty before calling a winner.

The query below compares measured session duration across the site. It excludes sessions with conflicting exposures and sessions active within the last 30 minutes. Returning visitors can contribute multiple sessions, so this descriptive report is not a visitor-level significance test; use PostHog's experiment analysis for inference.

```sql
SELECT
    exposure.variant,
    count() AS sessions,
    avg(s.$session_duration) AS average_seconds,
    quantile(0.5)(s.$session_duration) AS median_seconds
FROM sessions s
JOIN (
    SELECT
        properties.$session_id AS session_id,
        any(properties.variant) AS variant
    FROM events
    WHERE event = 'featured_sound_exposure'
      AND properties.experiment = 'homepage-featured-sound-v1'
      AND properties.variant IN ('control', 'endless-riser')
      AND timestamp >= now() - INTERVAL 30 DAY
    GROUP BY properties.$session_id
    HAVING count(DISTINCT properties.variant) = 1
) exposure ON s.session_id = exposure.session_id
WHERE s.$end_timestamp < now() - INTERVAL 30 MINUTE
GROUP BY exposure.variant
```

The client waits up to 1.5 seconds for flags, then freezes the displayed sound for that mount. Missing flags, blocked analytics, opted-out visitors, missing control content, and timeouts show Endless Riser without experiment exposure. A late flag does not replace a sound being played. No random client-side assignment is used: PostHog controls allocation.

Creating or launching the hosted experiment requires project access. Deploy the integration before starting the experiment. Without its flag, the new default is shown to everyone.

References: [PostHog experiments](https://posthog.com/docs/experiments), [session metrics](https://posthog.com/tutorials/session-metrics).
