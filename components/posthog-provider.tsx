"use client";

import type { ReactNode } from "react";

/** @deprecated PostHog boots from StatsProvider; kept for layout import stability. */
export function PosthogProvider({ children }: { children: ReactNode }) {
  return children;
}
