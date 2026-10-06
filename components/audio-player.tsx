"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import {
  getPlayingId,
  notifyEnded,
  registerAudioElement,
  requestPause,
  requestPlay,
  subscribePlayback,
} from "@/lib/audio-controller";
import { PlayPauseIcon } from "@/components/play-pause-icon";
import { EqualizerBars } from "@/components/equalizer-bars";
import { WaveformScrubber } from "@/components/waveform-scrubber";
import type { SoundEntry } from "@/lib/entries";
import { useSoundPlaybackAnalytics } from "@/lib/use-sound-playback-analytics";

type Props = {
  audioId: string;
  src: string;
  title: string;
  className?: string;
  entry: Pick<SoundEntry, "id" | "category" | "mood" | "modelId">;
};

export function AudioPlayer({ audioId, src, title, className, entry }: Props) {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [playing, setPlaying] = useState(false);
  const [progress, setProgress] = useState(0);

  useSoundPlaybackAnalytics(entry, "detail", audioRef, playing);

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
    const onTime = () => setProgress(el.duration ? el.currentTime / el.duration : 0);
    const onEnd = () => {
      notifyEnded(audioId);
      setPlaying(false);
      setProgress(0);
    };
    el.addEventListener("timeupdate", onTime);
    el.addEventListener("ended", onEnd);
    return () => {
      el.removeEventListener("timeupdate", onTime);
      el.removeEventListener("ended", onEnd);
    };
  }, [audioId]);

  const toggle = useCallback(async () => {
    if (getPlayingId() === audioId && playing) {
      requestPause(audioId);
    } else {
      try {
        await requestPlay(audioId);
      } catch {
        requestPause(audioId);
      }
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

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.code !== "Space" || e.target instanceof HTMLInputElement) return;
      if (document.activeElement?.closest("[data-audio-player]")) {
        e.preventDefault();
        void toggle();
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [toggle]);

  return (
    <div
      data-audio-player
      className={cn(
        "flex flex-col gap-3 rounded-xl border bg-zinc-900/60 p-4 transition-[border-color,box-shadow] duration-300",
        playing
          ? "border-violet-500/35 shadow-[0_0_0_1px_rgb(139_92_246/0.12)]"
          : "border-zinc-800",
        className,
      )}
    >
      <audio ref={audioRef} src={src} preload="metadata" title={title} />
      <div className="flex items-center gap-3">
        <Button
          type="button"
          variant="default"
          size="sm"
          onClick={() => void toggle()}
          aria-pressed={playing}
          aria-label={playing ? "Pause" : "Play"}
          className="active:scale-[0.97]"
        >
          <PlayPauseIcon playing={playing} />
          <span className="sr-only">{playing ? "Pause" : "Play"}</span>
        </Button>
        {playing && <EqualizerBars active className="h-4" />}
        <span className="text-xs text-zinc-600" title="Keyboard shortcut">
          Space
        </span>
      </div>
      <WaveformScrubber
        src={src}
        progress={progress}
        playing={playing}
        onSeek={seek}
      />
    </div>
  );
}
