"use client";

import { useEffect, useMemo, useRef } from "react";
import type { SoundEntry } from "@/lib/entries";
import { captureEvent } from "@/lib/analytics-client";
import { soundEventProps, type AnalyticsSource } from "@/lib/analytics";

export function useSoundPlaybackAnalytics(
  entry: Pick<SoundEntry, "id" | "category" | "mood" | "modelId">,
  source: AnalyticsSource,
  audioRef: React.RefObject<HTMLAudioElement | null>,
  playing: boolean,
) {
  const base = useMemo(() => soundEventProps(entry, source), [entry, source]);
  const wasPlaying = useRef(false);
  const seeked = useRef(false);

  useEffect(() => {
    if (playing && !wasPlaying.current) {
      captureEvent("sound_play", base);
    }
    wasPlaying.current = playing;
  }, [playing, base]);

  useEffect(() => {
    const el = audioRef.current;
    if (!el) return;

    const onEnded = () => {
      captureEvent("sound_complete", base);
    };

    const onSeeking = () => {
      seeked.current = true;
    };

    const onSeeked = () => {
      if (seeked.current) {
        seeked.current = false;
        captureEvent("sound_seek", {
          ...base,
          position_ratio: el.duration ? el.currentTime / el.duration : 0,
        });
      }
    };

    el.addEventListener("ended", onEnded);
    el.addEventListener("seeking", onSeeking);
    el.addEventListener("seeked", onSeeked);
    return () => {
      el.removeEventListener("ended", onEnded);
      el.removeEventListener("seeking", onSeeking);
      el.removeEventListener("seeked", onSeeked);
    };
  }, [audioRef, base]);
}
