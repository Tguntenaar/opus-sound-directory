"use client";

import type { PostHog } from "posthog-js";

let posthogRef: PostHog | null = null;

export function setPosthogClient(client: PostHog | null) {
  posthogRef = client;
}

export function getPosthogClient(): PostHog | null {
  return posthogRef;
}

/** Fire-and-forget client event; no-ops when PostHog is not initialized. */
export function captureEvent(
  event: string,
  properties?: Record<string, string | number | boolean | null | undefined | string[]>,
): void {
  const ph = posthogRef;
  if (!ph) return;
  ph.capture(event, properties);
}
