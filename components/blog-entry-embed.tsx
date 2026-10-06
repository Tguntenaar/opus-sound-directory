"use client";

import Link from "next/link";
import { useEffect, useRef, useState, type MouseEvent } from "react";
import type { SoundEntry } from "@/lib/entries";
import {
  getPlayingId,
  notifyEnded,
  registerAudioElement,
  requestPause,
  requestPlay,
  subscribePlayback,
} from "@/lib/audio-controller";
import { PlayPauseIcon } from "@/components/play-pause-icon";
import { useSoundPlaybackAnalytics } from "@/lib/use-sound-playback-analytics";

export function BlogEntryEmbed({ entry }: { entry: SoundEntry }) {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [playing, setPlaying] = useState(false);
  const audioId = entry.id;

  useSoundPlaybackAnalytics(entry, "blog_embed", audioRef, playing);

  useEffect(() => {
    const el = audioRef.current;
    if (!el) return;
    return registerAudioElement(audioId, el);
  }, [audioId]);

  useEffect(() => {
    return subscribePlayback((id) => setPlaying(id === audioId));
  }, [audioId]);

  async function onPlay(e: MouseEvent) {
    e.preventDefault();
    e.stopPropagation();
    if (getPlayingId() === audioId && playing) {
      requestPause(audioId);
      return;
    }
    try {
      await requestPlay(audioId);
    } catch {
      requestPause(audioId);
    }
  }

  return (
    <div
      className="not-prose my-6 flex items-center gap-3 rounded-lg border border-zinc-800/90 bg-zinc-900/30 px-3 py-2.5 transition-colors hover:border-zinc-700/90 motion-reduce:transition-none"
      data-sound-card
    >
      <audio
        ref={audioRef}
        src={entry.assets.mp3}
        preload="none"
        onEnded={() => notifyEnded(audioId)}
      />
      <button
        type="button"
        onClick={onPlay}
        className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-zinc-700 text-zinc-300 transition-[color,border-color,transform] duration-200 hover:border-violet-500/50 hover:text-violet-300 active:scale-95 motion-reduce:active:scale-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-violet-500/60"
        aria-label={playing ? `Pause ${entry.title}` : `Play ${entry.title}`}
      >
        <PlayPauseIcon playing={playing} className="h-3.5 w-3.5" />
      </button>
      <Link
        href={`/e/${entry.slug}`}
        className="min-w-0 flex-1 text-sm font-medium text-zinc-200 transition-colors hover:text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-violet-500/60"
      >
        {entry.title}
      </Link>
      <span className="shrink-0 text-xs tabular-nums text-zinc-600">
        {entry.timing.durationSec}s
      </span>
    </div>
  );
}
