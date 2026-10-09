"use client";

import type { ReactNode } from "react";
import { AuthCallbackAnalytics } from "@/components/auth-callback-analytics";

/** @deprecated PostHog boots from StatsProvider; kept for layout import stability. */
export function PosthogProvider({ children }: { children: ReactNode }) {
  return <><AuthCallbackAnalytics />{children}</>;
}
