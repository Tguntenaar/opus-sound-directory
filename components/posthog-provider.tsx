"use client";

import { Suspense, useEffect, type ReactNode } from "react";
import { usePathname, useSearchParams } from "next/navigation";
import { POSTHOG_UI_HOST, publicPosthogKey } from "@/lib/posthog-config";
import { setPosthogClient } from "@/lib/analytics-client";

function PosthogPageviews() {
  const pathname = usePathname();
  const searchParams = useSearchParams();

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      const { default: posthog } = await import("posthog-js");
      if (cancelled || !publicPosthogKey()) return;
      const search = searchParams?.toString();
      const url = search ? `${pathname}?${search}` : pathname;
      posthog.capture("$pageview", { $current_url: url });
    })();
    return () => {
      cancelled = true;
    };
  }, [pathname, searchParams]);

  return null;
}

export function PosthogProvider({ children }: { children: ReactNode }) {
  useEffect(() => {
    const key = publicPosthogKey();
    if (!key) {
      setPosthogClient(null);
      return;
    }

    let cancelled = false;
    void (async () => {
      const { default: posthog } = await import("posthog-js");
      if (cancelled) return;

      posthog.init(key, {
        api_host: "/ingest",
        ui_host: POSTHOG_UI_HOST,
        capture_pageview: false,
        capture_pageleave: true,
        autocapture: true,
        respect_dnt: true,
        persistence: "localStorage+cookie",
        person_profiles: "identified_only",
      });

      setPosthogClient(posthog);
    })();

    return () => {
      cancelled = true;
      setPosthogClient(null);
    };
  }, []);

  return (
    <>
      <Suspense fallback={null}>
        <PosthogPageviews />
      </Suspense>
      {children}
    </>
  );
}
