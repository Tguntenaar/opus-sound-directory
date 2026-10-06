"use client";

import Link from "next/link";
import { Pause, Play } from "lucide-react";
import type { SoundEntry } from "@/lib/entries";
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
import { MoodChips } from "@/components/mood-chips";
import { ModelBadge } from "@/components/model-badge";

export function EntryCard({ entry }: { entry: SoundEntry }) {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [playing, setPlaying] = useState(false);
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
      className="group flex flex-col gap-4 rounded-lg border border-zinc-800/80 bg-zinc-900/20 p-4 transition-colors hover:border-zinc-700 hover:bg-zinc-900/40"
    >
      <audio
        ref={audioRef}
        src={entry.assets.wav}
        preload="none"
        onEnded={() => notifyEnded(audioId)}
      />
      <div className="flex items-start gap-3">
        <button
          type="button"
          onClick={playPreview}
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-zinc-700 text-zinc-300 transition-colors hover:border-violet-500/50 hover:text-violet-300"
          aria-label={playing ? `Stop preview of ${entry.title}` : `Preview ${entry.title}`}
        >
          {playing ? <Pause className="h-3.5 w-3.5" /> : <Play className="h-3.5 w-3.5" />}
        </button>
        <h3 className="min-w-0 flex-1 pt-0.5 text-sm font-medium leading-snug text-zinc-100 group-hover:text-white">
          {entry.title}
        </h3>
      </div>
      <MoodChips entry={entry} compact />
      <div className="flex items-end justify-between gap-2">
        <ModelBadge entry={entry} chip />
        <UsageBadges entryId={entry.id} compact className="text-[10px] text-zinc-600" />
      </div>
    </Link>
  );
}
