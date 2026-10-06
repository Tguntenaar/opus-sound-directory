/** PostHog US cloud defaults; override region via NEXT_PUBLIC_POSTHOG_HOST. */

export const POSTHOG_UI_HOST = "https://us.posthog.com";

export function posthogIngestApiHost(): string {
  return (
    process.env.NEXT_PUBLIC_POSTHOG_HOST?.trim() || "https://us.i.posthog.com"
  ).replace(/\/$/, "");
}

export function posthogAssetsHost(): string {
  const api = posthogIngestApiHost();
  if (api.includes("eu.i.posthog.com")) return "https://eu-assets.i.posthog.com";
  return "https://us-assets.i.posthog.com";
}

export function publicPosthogKey(): string | undefined {
  const key = process.env.NEXT_PUBLIC_POSTHOG_KEY?.trim();
  return key || undefined;
}

/** Worker / server capture — secret preferred, else build-inlined public key. */
export function serverPosthogKey(): string | undefined {
  const secret = process.env.POSTHOG_KEY?.trim();
  if (secret) return secret;
  return publicPosthogKey();
}
