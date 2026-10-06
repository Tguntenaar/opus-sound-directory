"use client";

import { useEffect } from "react";
import { usePathname } from "next/navigation";
import { getPosthogWhenReady } from "@/lib/analytics-client";

export function PosthogPageviews() {
  const pathname = usePathname();

  useEffect(() => {
    void getPosthogWhenReady().then((ph) => {
      if (!ph) return;
      const search = typeof window !== "undefined" ? window.location.search : "";
      const hash = typeof window !== "undefined" ? window.location.hash : "";
      const pathWithQuery = search ? `${pathname}${search}` : pathname;
      const url = hash ? `${pathWithQuery}${hash}` : pathWithQuery;
      queueMicrotask(() => {
        ph.capture("$pageview", { $current_url: url });
      });
    });
  }, [pathname]);

  return null;
}
