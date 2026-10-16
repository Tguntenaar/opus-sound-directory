"use client";

import { useEffect, useRef, useState } from "react";
import type { SoundEntry } from "@/lib/entries-types";
import {
  FEATURED_ENTRY_SLUG,
  FEATURED_EXPERIMENT_FLAG,
  canApplyFeaturedVariant,
  featuredVariant,
  resolveFeaturedSound,
} from "@/lib/featured";
import { subscribePlayback } from "@/lib/audio-controller";
import { FeaturedSlot } from "@/components/featured-slot";

/** Editorial default on first paint; PostHog may reassign within 1.5s unless playback started. */
export function FeaturedSoundExperiment({ entry, control }: { entry: SoundEntry; control?: SoundEntry }) {
  const ref = useRef<HTMLDivElement>(null);
  const playbackLockedRef = useRef(false);
  const [selection, setSelection] = useState<{ variant: ReturnType<typeof featuredVariant> }>({ variant: null });
  const selectionRef = useRef(selection);
  selectionRef.current = selection;

  const selected = resolveFeaturedSound(selection.variant, entry, control);
  const selectedIdRef = useRef(selected.id);
  selectedIdRef.current = selected.id;

  useEffect(() => {
    return subscribePlayback((id) => {
      if (!id) return;
      const displayed = selectedIdRef.current;
      if (id === displayed || id.startsWith(`${displayed}:`)) playbackLockedRef.current = true;
    });
  }, []);

  useEffect(() => {
    let finished = false;
    let unsubscribe: (() => void) | undefined;
    const choose = (variant: ReturnType<typeof featuredVariant>) => {
      if (finished) return;
      const current = resolveFeaturedSound(selectionRef.current.variant, entry, control);
      if (!canApplyFeaturedVariant(variant, current, entry, control, playbackLockedRef.current)) return;
      finished = true;
      setSelection({ variant });
    };
    const timeout = setTimeout(() => choose(null), 1500);
    void import("@/lib/posthog-browser").then(({ getPosthogWhenReady }) => getPosthogWhenReady()).then((ph) => {
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

  useEffect(() => {
    if (!selection.variant || !ref.current) return;
    let disposed = false;
    let visible = false;
    let fired = false;
    const expose = () => {
      if (fired || !visible || document.visibilityState !== "visible") return;
      fired = true;
      observer.disconnect();
      void import("@/lib/posthog-browser").then(({ getPosthogWhenReady }) => getPosthogWhenReady()).then((ph) => {
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

  return (
    <div ref={ref}>
      <FeaturedSlot entry={selected} placement="home" />
    </div>
  );
}
