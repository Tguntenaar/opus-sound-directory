"use client";

import {
  captureWhenReady,
  getPosthogClient,
  getPosthogWhenReady,
} from "@/lib/posthog-browser";

/** Fire-and-forget client event; waits for PostHog init when needed. */
export function captureEvent(
  event: string,
  properties?: Record<string, string | number | boolean | null | undefined | string[]>,
): void {
  const ph = getPosthogClient();
  if (ph) {
    ph.capture(event, properties);
    return;
  }
  captureWhenReady(event, properties);
}

/** Ensure SDK is initialized (e.g. provider mount). */
export { getPosthogWhenReady };
