"use client";

import Link from "next/link";
import { Pause, Play } from "lucide-react";
import type { SoundEntry } from "@/lib/entries";
import { CATEGORIES } from "@/lib/categories";
import { useEffect, useRef, useState, type MouseEvent } from "react";
import {
  getPlayingId,
  notifyEnded,
  registerAudioElement,
  requestPause,
  requestPlay,
  subscribePlayback,
} from "@/lib/audio-controller";
import { UsageBadges } from "@/components/usage-badges";

export function EntryCard({ entry }: { entry: SoundEntry }) {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [playing, setPlaying] = useState(false);
  const cat = CATEGORIES[entry.category]?.label ?? entry.category;
  const audioId = entry.id;

  useEffect(() => {
    const el = audioRef.current;
    if (!el) return;
    return registerAudioElement(audioId, el);
  }, [audioId]);

  useEffect(() => {
    return subscribePlayback((id) => setPlaying(id === audioId));
  }, [audioId]);

  async function playPreview(e: MouseEvent) {
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
    <Link
      href={`/e/${entry.slug}`}
      className="group flex flex-col gap-3 rounded-xl border border-zinc-800 bg-zinc-900/40 p-4 transition hover:border-violet-500/40 hover:bg-zinc-900/70"
    >
      <audio
        ref={audioRef}
        src={entry.assets.wav}
        preload="none"
        onEnded={() => notifyEnded(audioId)}
      />
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <h3 className="font-medium text-zinc-100 group-hover:text-white">{entry.title}</h3>
          <p className="mt-1 text-xs text-zinc-500">{cat}</p>
          <UsageBadges entryId={entry.id} className="mt-2" compact />
        </div>
        <button
          type="button"
          onClick={playPreview}
          className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-zinc-700 bg-zinc-950 text-zinc-200 hover:border-violet-500 hover:text-violet-300"
          aria-label={playing ? `Stop preview of ${entry.title}` : `Preview ${entry.title}`}
        >
          {playing ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
        </button>
      </div>
      <div className="flex flex-wrap gap-1.5">
        {entry.tags.slice(0, 3).map((tag) => (
          <span
            key={tag}
            className="rounded-md bg-zinc-800/80 px-2 py-0.5 text-[10px] uppercase tracking-wide text-zinc-400"
          >
            {tag}
          </span>
        ))}
      </div>
    </Link>
  );
}
