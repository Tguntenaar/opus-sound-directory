"use client";

import { POSTHOG_UI_HOST } from "@/lib/posthog-config";
import { CLIENT_POSTHOG_KEY } from "@/lib/posthog-public-key";

type PostHogClient = import("posthog-js").default;

let posthogRef: PostHogClient | null = null;
let initPromise: Promise<PostHogClient | null> | null = null;
/**
 * PostHog capture endpoints must not pass through vinext trailing-slash 308
 * redirects (POST → GET). `/api/*` is exempt from those redirects.
 */
export const POSTHOG_API_HOST = "/api/ingest";

export function publicPosthogKeyClient(): string | undefined {
  return CLIENT_POSTHOG_KEY || undefined;
}

export function getPosthogClient(): PostHogClient | null {
  return posthogRef;
}

export function getPosthogWhenReady(): Promise<PostHogClient | null> {
  if (typeof window === "undefined") return Promise.resolve(null);
  const key = publicPosthogKeyClient();
  if (!key) return Promise.resolve(null);

  if (posthogRef?.__loaded) return Promise.resolve(posthogRef);

  if (!initPromise) {
    initPromise = import("posthog-js").then((mod) => {
      const posthog = mod.default;
      return new Promise<PostHogClient | null>((resolve) => {
        if (posthog.__loaded) {
          posthogRef = posthog;
          resolve(posthog);
          return;
        }

        const isPlaywrightTestKey = key === "phc_playwright_test_key";

        posthog.init(key, {
          api_host: POSTHOG_API_HOST,
          ui_host: POSTHOG_UI_HOST,
          capture_pageview: false,
          capture_pageleave: true,
          autocapture: true,
          opt_out_useragent_filter: isPlaywrightTestKey,
          respect_dnt: true,
          persistence: "localStorage+cookie",
          person_profiles: "identified_only",
          loaded: (ph) => {
            posthogRef = ph;
            if (typeof window !== "undefined") {
              (window as unknown as { posthog?: PostHogClient }).posthog = ph;
            }
            resolve(ph);
          },
        });
      });
    });
  }
  return initPromise;
}

export function captureWhenReady(
  event: string,
  properties?: Record<string, string | number | boolean | null | undefined | string[]>,
): void {
  void getPosthogWhenReady().then((ph) => {
    if (!ph) return;
    ph.capture(event, properties);
  });
}
