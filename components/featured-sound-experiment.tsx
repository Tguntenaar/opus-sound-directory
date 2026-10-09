"use client";

import { useEffect, useRef, useState } from "react";
import type { SoundEntry } from "@/lib/entries-types";
import { getPosthogWhenReady } from "@/lib/posthog-browser";
import { FEATURED_ENTRY_SLUG, FEATURED_EXPERIMENT_FLAG, featuredVariant } from "@/lib/featured";
import { FeaturedSlot } from "@/components/featured-slot";

/** Freeze the assignment before showing the card; late flags never swap a playing sound. */
export function FeaturedSoundExperiment({ entry, control }: { entry: SoundEntry; control?: SoundEntry }) {
  const ref = useRef<HTMLDivElement>(null);
  const [selection, setSelection] = useState<{ variant: ReturnType<typeof featuredVariant> } | null>(null);

  useEffect(() => {
    let finished = false;
    let unsubscribe: (() => void) | undefined;
    const choose = (variant: ReturnType<typeof featuredVariant>) => {
      if (finished) return;
      finished = true;
      setSelection({ variant });
    };
    const timeout = setTimeout(() => choose(null), 1500);
    void getPosthogWhenReady().then((ph) => {
      if (finished) return;
      if (!ph || ph.has_opted_out_capturing() || !control || entry.slug !== FEATURED_ENTRY_SLUG) return choose(null);
      const read = () => featuredVariant(ph.getFeatureFlag(FEATURED_EXPERIMENT_FLAG, { send_event: false }));
      const cached = read();
      if (cached) return choose(cached);
      unsubscribe = ph.onFeatureFlags(() => choose(read()));
    });
    return () => {
      finished = true;
      clearTimeout(timeout);
      unsubscribe?.();
    };
  }, [control, entry.slug]);

  const selected = selection?.variant === "control" && control ? control : entry;
  useEffect(() => {
    if (!selection?.variant || !ref.current) return;
    let disposed = false;
    let visible = false;
    let fired = false;
    const expose = () => {
      if (fired || !visible || document.visibilityState !== "visible") return;
      fired = true;
      observer.disconnect();
      void getPosthogWhenReady().then((ph) => {
        if (disposed || !ph || ph.has_opted_out_capturing()) return;
        const session = ph.get_session_id();
        const key = `${FEATURED_EXPERIMENT_FLAG}:${session}`;
        try {
          if (sessionStorage.getItem(key)) return;
          sessionStorage.setItem(key, "1");
        } catch { /* Collection still works when storage is unavailable. */ }
        ph.capture("featured_sound_exposure", {
          experiment: FEATURED_EXPERIMENT_FLAG,
          variant: selection.variant,
          [`$feature/${FEATURED_EXPERIMENT_FLAG}`]: selection.variant,
          sound_id: selected.id,
          sound_slug: selected.slug,
          placement: "home",
        });
      });
    };
    const observer = new IntersectionObserver(([intersection]) => {
      visible = !!intersection && intersection.intersectionRatio >= 0.5;
      expose();
    }, { threshold: 0.5 });
    observer.observe(ref.current);
    document.addEventListener("visibilitychange", expose);
    return () => {
      disposed = true;
      observer.disconnect();
      document.removeEventListener("visibilitychange", expose);
    };
  }, [selection, selected.id, selected.slug]);

  return <div ref={ref}>
    {selection ? <FeaturedSlot entry={selected} placement="home" /> :
      <div className="min-h-64 rounded-xl border border-violet-500/20 bg-zinc-900/30" aria-busy="true" aria-label="Loading featured sound" />}
  </div>;
}
