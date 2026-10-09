"use client";

import { useEffect } from "react";
import { usePathname } from "next/navigation";
import { getPosthogWhenReady } from "@/lib/analytics-client";

export function PosthogPageviews() {
  const pathname = usePathname();

  useEffect(() => {
    void getPosthogWhenReady().then((ph) => {
      if (!ph) return;
      const params = new URLSearchParams(typeof window !== "undefined" ? window.location.search : "");
      for (const key of ["code", "state", "error", "error_description", "sign_in"]) params.delete(key);
      const search = params.size ? `?${params.toString()}` : "";
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
