"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Pause, Play } from "lucide-react";
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

type Props = {
  audioId: string;
  src: string;
  title: string;
  className?: string;
};

export function AudioPlayer({ audioId, src, title, className }: Props) {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [playing, setPlaying] = useState(false);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const el = audioRef.current;
    if (!el) return;
    return registerAudioElement(audioId, el);
  }, [audioId]);

  useEffect(() => {
    return subscribePlayback((id) => {
      setPlaying(id === audioId);
    });
  }, [audioId]);

  useEffect(() => {
    const el = audioRef.current;
    if (!el) return;
    const onTime = () => setProgress(el.duration ? el.currentTime / el.duration : 0);
    const onEnd = () => {
      notifyEnded(audioId);
      setPlaying(false);
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
        "flex flex-col gap-3 rounded-xl border border-zinc-800 bg-zinc-900/60 p-4",
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
        >
          {playing ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
          {playing ? "Pause" : "Play"}
        </Button>
        <span className="text-sm text-zinc-400">Space to play/pause when focused</span>
      </div>
      <div
        className="h-1.5 overflow-hidden rounded-full bg-zinc-800"
        role="progressbar"
        aria-valuenow={Math.round(progress * 100)}
        aria-valuemin={0}
        aria-valuemax={100}
      >
        <div
          className="h-full bg-violet-500 transition-[width] duration-150"
          style={{ width: `${progress * 100}%` }}
        />
      </div>
    </div>
  );
}
