"use client";

/** Fire-and-forget client event; waits for PostHog init when needed. */
export function captureEvent(
  event: string,
  properties?: Record<string, string | number | boolean | null | undefined | string[]>,
): void {
  void import("@/lib/posthog-browser").then(({ getPosthogClient, captureWhenReady }) => {
    const ph = getPosthogClient();
    if (ph) {
      ph.capture(event, properties);
      return;
    }
    captureWhenReady(event, properties);
  });
}

/** Ensure SDK is initialized (e.g. provider mount). */
export function getPosthogWhenReady(): Promise<import("posthog-js").default | null> {
  return import("@/lib/posthog-browser").then((m) => m.getPosthogWhenReady());
}
