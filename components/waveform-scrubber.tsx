"use client";

import { useCallback, useEffect, useRef, useState, type MouseEvent } from "react";
import { loadWaveformPeaks } from "@/lib/waveform-peaks";
import { cn } from "@/lib/utils";

type Props = {
  src: string;
  progress: number;
  playing: boolean;
  onSeek: (ratio: number) => void;
  className?: string;
  compact?: boolean;
};

export function WaveformScrubber({
  src,
  progress,
  playing,
  onSeek,
  className,
  compact = false,
}: Props) {
  const railRef = useRef<HTMLDivElement>(null);
  const [peaks, setPeaks] = useState<number[] | null>(null);
  const [hoverRatio, setHoverRatio] = useState<number | null>(null);
  const [loadPeaks, setLoadPeaks] = useState(false);

  useEffect(() => {
    const rail = railRef.current;
    if (!rail || loadPeaks) return;
    const io = new IntersectionObserver(
      ([entry]) => {
        if (entry?.isIntersecting) {
          setLoadPeaks(true);
          io.disconnect();
        }
      },
      { rootMargin: "120px" },
    );
    io.observe(rail);
    return () => io.disconnect();
  }, [loadPeaks]);

  useEffect(() => {
    if (!loadPeaks) return;
    let cancelled = false;
    void loadWaveformPeaks(src).then((p) => {
      if (!cancelled) setPeaks(p);
    });
    return () => {
      cancelled = true;
    };
  }, [src, loadPeaks]);

  const ratioFromEvent = useCallback((e: MouseEvent<HTMLDivElement>) => {
    const rail = railRef.current;
    if (!rail) return 0;
    const rect = rail.getBoundingClientRect();
    const x = Math.min(rect.width, Math.max(0, e.clientX - rect.left));
    return rect.width ? x / rect.width : 0;
  }, []);

  function onMove(e: MouseEvent<HTMLDivElement>) {
    setHoverRatio(ratioFromEvent(e));
  }

  function onLeave() {
    setHoverRatio(null);
  }

  function onClick(e: MouseEvent<HTMLDivElement>) {
    e.preventDefault();
    e.stopPropagation();
    onSeek(ratioFromEvent(e));
  }

  const playhead = hoverRatio ?? progress;
  const height = compact ? "h-7" : "h-10";

  return (
    <div
      ref={railRef}
      role="slider"
      aria-label="Audio waveform"
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={Math.round((playing ? progress : playhead) * 100)}
      tabIndex={0}
      onMouseMove={onMove}
      onMouseLeave={onLeave}
      onClick={onClick}
      onKeyDown={(e) => {
        if (e.key === "ArrowLeft") {
          e.preventDefault();
          e.stopPropagation();
          onSeek(Math.max(0, progress - 0.05));
        }
        if (e.key === "ArrowRight") {
          e.preventDefault();
          e.stopPropagation();
          onSeek(Math.min(1, progress + 0.05));
        }
      }}
      className={cn(
        "relative w-full cursor-pointer overflow-hidden rounded-md bg-zinc-950/50 ring-1 ring-inset ring-zinc-800/80 transition-colors hover:ring-zinc-600/60",
        height,
        className,
      )}
    >
      <div className="absolute inset-0 flex items-end gap-[1px] px-1 py-1.5">
        {(peaks ?? Array.from({ length: 48 }, () => 0.3)).map((p, i) => {
          const barProgress = (i + 0.5) / (peaks?.length ?? 48);
          const lit = barProgress <= progress;
          const hoverLit = hoverRatio !== null && barProgress <= hoverRatio;
          return (
            <span
              key={i}
              className={cn(
                "flex-1 rounded-[1px] transition-colors duration-75",
                lit || (playing && hoverLit)
                  ? "bg-violet-400/85"
                  : hoverLit
                    ? "bg-violet-400/35"
                    : "bg-zinc-600/55",
              )}
              style={{ height: `${Math.max(12, p * 100)}%` }}
            />
          );
        })}
      </div>
      {playhead > 0 && (
        <span
          className="pointer-events-none absolute inset-y-1 w-px bg-violet-200/70 shadow-[0_0_6px_rgb(196_181_253/0.45)]"
          style={{ left: `calc(${playhead * 100}% - 0.5px)` }}
          aria-hidden
        />
      )}
    </div>
  );
}
