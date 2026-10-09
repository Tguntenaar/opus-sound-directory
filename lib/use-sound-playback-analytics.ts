"use client";

import { useEffect, useMemo } from "react";
import type { SoundEntry } from "@/lib/entries";
import { captureEvent } from "@/lib/analytics-client";
import { soundEventProps, type AnalyticsSource } from "@/lib/analytics";
import { useStats } from "@/components/stats-provider";

export function useSoundPlaybackAnalytics(
  entry: Pick<SoundEntry, "id" | "category" | "mood" | "modelId">,
  source: AnalyticsSource,
  audioRef: React.RefObject<HTMLAudioElement | null>,
  _playing: boolean,
) {
  const base = useMemo(() => soundEventProps(entry, source), [entry, source]);
  const { track } = useStats();

  useEffect(() => {
    const el = audioRef.current;
    if (!el) return;
    let started = false;
    let seeking = false;
    let completed = false;
    const milestones = new Set<number>();
    const position = () => Number.isFinite(el.duration) && el.duration > 0
      ? Math.min(1, el.currentTime / el.duration) : 0;
    // The media event confirms audible playback; controller state also changes
    // before play() succeeds and must not be counted as a successful listen.
    const onPlaying = () => {
      if (started) return;
      started = true;
      completed = false;
      captureEvent("sound_play", base);
      track(entry.id, "play");
    };
    const onEnded = () => {
      if (!started || completed) return;
      completed = true;
      captureEvent("sound_complete", base);
      started = false;
      milestones.clear();
    };
    const onSeeking = () => { seeking = true; };
    const onSeeked = () => {
      seeking = false;
      // Seeking past a milestone is not evidence that it was listened to.
      for (const milestone of [25, 50, 75]) {
        if (position() >= milestone / 100) milestones.add(milestone);
      }
      captureEvent("sound_seek", { ...base, position_ratio: position() });
    };
    const onTime = () => {
      if (!started || seeking || el.paused) return;
      const progress = position();
      for (const milestone of [25, 50, 75]) {
        if (progress >= milestone / 100 && !milestones.has(milestone)) {
          milestones.add(milestone);
          captureEvent("sound_progress", { ...base, percent: milestone });
        }
      }
    };
    const onError = () => captureEvent("sound_play_error", {
      ...base, error_code: el.error?.code ?? 0,
    });
    el.addEventListener("playing", onPlaying);
    el.addEventListener("ended", onEnded);
    el.addEventListener("seeking", onSeeking);
    el.addEventListener("seeked", onSeeked);
    el.addEventListener("timeupdate", onTime);
    el.addEventListener("error", onError);
    return () => {
      el.removeEventListener("playing", onPlaying);
      el.removeEventListener("ended", onEnded);
      el.removeEventListener("seeking", onSeeking);
      el.removeEventListener("seeked", onSeeked);
      el.removeEventListener("timeupdate", onTime);
      el.removeEventListener("error", onError);
    };
  }, [audioRef, base, entry.id, track]);
}
