/** Build-time inlined public PostHog key (client bundles only). */
export const CLIENT_POSTHOG_KEY = (process.env.NEXT_PUBLIC_POSTHOG_KEY ?? "").trim();
