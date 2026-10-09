"use client";

import Link from "next/link";
import type { SoundEntry } from "@/lib/entries";
import { useCallback, useEffect, useRef, useState, type KeyboardEvent, type MouseEvent } from "react";
import {
  getPlayingId,
  notifyEnded,
  registerAudioElement,
  requestPause,
  requestPlay,
  subscribePlayback,
} from "@/lib/audio-controller";
import { setFocusedSoundCard } from "@/lib/playback-focus";
import { UsageBadges } from "@/components/usage-badges";
import { MoodChips } from "@/components/mood-chips";
import { ModelBadge } from "@/components/model-badge";
import { EntryTakeAffordance } from "@/components/entry-take-affordance";
import { useResolvedEntryTake } from "@/lib/use-resolved-entry-take";
import { PlayPauseIcon } from "@/components/play-pause-icon";
import { EqualizerBars } from "@/components/equalizer-bars";
import { WaveformScrubber } from "@/components/waveform-scrubber";
import { CardQuickActions } from "@/components/card-quick-actions";
import { cn } from "@/lib/utils";
import { useSoundPlaybackAnalytics } from "@/lib/use-sound-playback-analytics";
import { soundEventProps, type AnalyticsSource } from "@/lib/analytics";
import { captureEvent } from "@/lib/analytics-client";

type Props = {
  entry: SoundEntry;
  staggerIndex?: number;
  featured?: boolean;
};

export function EntryCard({ entry, staggerIndex = 0, featured = false }: Props) {
  const cardRef = useRef<HTMLAnchorElement>(null);
  const impressionSent = useRef(false);
  const audioRef = useRef<HTMLAudioElement>(null);
  const [playing, setPlaying] = useState(false);
  const [progress, setProgress] = useState(0);
  const { defaultTake, hasTakes } = useResolvedEntryTake(entry);
  const previewSrc = defaultTake?.mp3 ?? entry.assets.mp3 ?? "";
  const previewEntry = defaultTake
    ? { ...entry, modelId: defaultTake.modelId }
    : entry;
  const audioId = hasTakes && defaultTake ? `${entry.id}:${defaultTake.id}` : entry.id;
  const analyticsSource: AnalyticsSource = featured ? "featured" : "card";

  useSoundPlaybackAnalytics(previewEntry, analyticsSource, audioRef, playing);

  useEffect(() => {
    const card = cardRef.current;
    if (!card || impressionSent.current || typeof IntersectionObserver === "undefined") return;
    const observer = new IntersectionObserver(([visible]) => {
      if (!visible?.isIntersecting || impressionSent.current) return;
      impressionSent.current = true;
      captureEvent("sound_impression", {
        ...soundEventProps(entry, analyticsSource), position: staggerIndex + 1,
      });
      observer.disconnect();
    }, { threshold: 0.5 });
    observer.observe(card);
    return () => observer.disconnect();
  }, [entry, analyticsSource, staggerIndex]);

  useEffect(() => {
    const el = audioRef.current;
    if (!el) return;
    return registerAudioElement(audioId, el);
  }, [audioId]);

  useEffect(() => {
    return subscribePlayback((id) => {
      const isPlaying = id === audioId;
      setPlaying(isPlaying);
      if (!isPlaying) setProgress(0);
    });
  }, [audioId]);

  useEffect(() => {
    const el = audioRef.current;
    if (!el) return;
    const onTime = () => {
      setProgress(el.duration ? el.currentTime / el.duration : 0);
    };
    el.addEventListener("timeupdate", onTime);
    return () => el.removeEventListener("timeupdate", onTime);
  }, [audioId]);

  const togglePlay = useCallback(async () => {
    if (getPlayingId() === audioId && playing) {
      requestPause(audioId);
      return;
    }
    try {
      await requestPlay(audioId);
    } catch {
      requestPause(audioId);
    }
  }, [audioId, playing]);

  const seek = useCallback(
    (ratio: number) => {
      const el = audioRef.current;
      if (!el) return;
      const clamped = Math.min(1, Math.max(0, ratio));
      if (el.duration) el.currentTime = clamped * el.duration;
      setProgress(clamped);
      if (!playing) void requestPlay(audioId);
    },
    [audioId, playing],
  );

  async function playPreview(e: MouseEvent) {
    e.preventDefault();
    e.stopPropagation();
    await togglePlay();
  }

  function onCardKeyDown(e: KeyboardEvent<HTMLAnchorElement>) {
    if (e.code === "Space") {
      e.preventDefault();
      void togglePlay();
    }
  }

  function onFocus() {
    setFocusedSoundCard(audioId);
  }

  function onBlur() {
    setFocusedSoundCard(null);
  }

  const staggerStyle =
    staggerIndex > 0
      ? { animationDelay: `${Math.min(staggerIndex * 45, 400)}ms` }
      : undefined;

  return (
    <Link
      ref={cardRef}
      onClick={() => captureEvent("sound_detail_click", { ...soundEventProps(entry, analyticsSource), position: staggerIndex + 1 })}
      href={`/e/${entry.slug}`}
      data-sound-card
      data-entry-id={audioId}
      onKeyDown={onCardKeyDown}
      onFocus={onFocus}
      onBlur={onBlur}
      style={staggerStyle}
      className={cn(
        "sound-card group relative flex cursor-pointer flex-col gap-3 overflow-hidden rounded-lg border bg-zinc-900/20 p-4 outline-none transition-[transform,box-shadow,border-color,background-color] duration-200 ease-out motion-reduce:transition-none",
        "border-zinc-800/80 hover:-translate-y-0.5 hover:border-zinc-600/90 hover:bg-zinc-900/45 hover:shadow-[0_8px_30px_-12px_rgb(0_0_0/0.55)]",
        "focus-visible:ring-2 focus-visible:ring-violet-500/50 focus-visible:ring-offset-2 focus-visible:ring-offset-zinc-950",
        playing &&
          "border-violet-500/35 bg-zinc-900/50 shadow-[0_0_0_1px_rgb(139_92_246/0.15),0_12px_40px_-16px_rgb(139_92_246/0.25)]",
        featured && "border-violet-500/25",
      )}
    >
      <audio
        ref={audioRef}
        src={previewSrc}
        preload="none"
        onEnded={() => {
          notifyEnded(audioId);
          setProgress(0);
        }}
      />
      <div className="flex items-start gap-2">
        <button
          type="button"
          onClick={playPreview}
          className={cn(
            "flex h-10 w-10 shrink-0 items-center justify-center rounded-full border transition-[border-color,background-color,transform] duration-200 active:scale-95",
            playing
              ? "border-violet-500/50 bg-violet-500/10 text-violet-200"
              : "border-zinc-700 text-zinc-300 hover:border-violet-500/50 hover:bg-zinc-900/80 hover:text-violet-300",
          )}
          aria-label={playing ? `Pause preview of ${entry.title}` : `Preview ${entry.title}`}
        >
          <PlayPauseIcon playing={playing} size="sm" />
        </button>
        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-2">
            <h3 className="text-sm font-medium leading-snug text-zinc-100 transition-colors group-hover:text-white">
              {entry.title}
            </h3>
            <div className="flex shrink-0 items-center gap-1">
              <EntryTakeAffordance entry={entry} />
              {playing && <EqualizerBars active className="mt-0.5" />}
              <CardQuickActions entry={entry} source={analyticsSource} />
            </div>
          </div>
        </div>
      </div>

      <WaveformScrubber
        src={previewSrc || entry.assets.wav}
        progress={progress}
        playing={playing}
        onSeek={seek}
        compact
      />

      <MoodChips entry={entry} compact />
      <div className="flex items-end justify-between gap-2">
        <ModelBadge entry={previewEntry} chip />
        <UsageBadges entryId={entry.id} compact className="text-xs text-zinc-600" />
      </div>
    </Link>
  );
}
