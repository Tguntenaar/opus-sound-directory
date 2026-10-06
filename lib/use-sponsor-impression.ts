"use client";

import { useEffect, type RefObject } from "react";
import { captureEvent } from "@/lib/analytics-client";

export const SPONSOR_IMPRESSION_RATIO = 0.5;
export const SPONSOR_IMPRESSION_MS = 1000;

export type SponsorSlotPlacement = "home" | "category";

/** Fire `sponsor_impression` once when the slot stays ≥50% visible for ~1s. */
export function useSponsorImpression(
  ref: RefObject<Element | null>,
  enabled: boolean,
  properties: { placement: SponsorSlotPlacement; category?: string },
): void {
  const { placement, category } = properties;

  useEffect(() => {
    const el = ref.current;
    if (!el || !enabled) return;

    let visibleSince: number | null = null;
    let timer: ReturnType<typeof setTimeout> | null = null;
    let fired = false;

    const clearTimer = () => {
      if (!timer) return;
      clearTimeout(timer);
      timer = null;
    };

    const fire = () => {
      if (fired) return;
      fired = true;
      clearTimer();
      captureEvent("sponsor_impression", {
        placement,
        ...(category ? { category } : {}),
      });
      io.disconnect();
    };

    const io = new IntersectionObserver(
      ([entry]) => {
        if (fired || !entry) return;
        if (entry.isIntersecting && entry.intersectionRatio >= SPONSOR_IMPRESSION_RATIO) {
          if (visibleSince == null) visibleSince = Date.now();
          const remaining = SPONSOR_IMPRESSION_MS - (Date.now() - visibleSince);
          if (remaining <= 0) {
            fire();
            return;
          }
          if (!timer) timer = setTimeout(fire, remaining);
          return;
        }
        visibleSince = null;
        clearTimer();
      },
      { threshold: [0, SPONSOR_IMPRESSION_RATIO, 1] },
    );

    io.observe(el);
    return () => {
      io.disconnect();
      clearTimer();
    };
  }, [enabled, placement, category, ref]);
}
