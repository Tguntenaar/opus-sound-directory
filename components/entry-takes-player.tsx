"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ThumbsUp } from "lucide-react";
import type { SoundEntry } from "@/lib/entries";
import { AudioPlayer } from "@/components/audio-player";
import { ModelBadge } from "@/components/model-badge";
import { useTakeVotes } from "@/components/take-votes-provider";
import { entryTakesFor } from "@/lib/hero8-takes";
import type { EntryTakeId } from "@/lib/hero8-takes-types";
import { pickDefaultTake, pickDefaultTakeId } from "@/lib/take-selection";
import { cn } from "@/lib/utils";

type Props = {
  entry: SoundEntry;
};

export function EntryTakesPlayer({ entry }: Props) {
  const takes = useMemo(() => entryTakesFor(entry), [entry]);
  const { getVotes, voteForTake } = useTakeVotes();
  const votes = getVotes(entry.id);
  const votedDefaultId = useMemo(
    () => pickDefaultTakeId(takes, votes),
    [takes, votes],
  );

  const [selectedId, setSelectedId] = useState<EntryTakeId>(votedDefaultId);
  const userPicked = useRef(false);

  useEffect(() => {
    if (!userPicked.current) setSelectedId(votedDefaultId);
  }, [votedDefaultId]);

  const activeTake = useMemo(
    () => takes.find((t) => t.id === selectedId) ?? pickDefaultTake(takes, votes),
    [takes, votes, selectedId],
  );

  const playbackEntry = useMemo(
    () => ({ ...entry, modelId: activeTake?.modelId ?? entry.modelId }),
    [entry, activeTake],
  );

  const onVote = useCallback(
    (takeId: EntryTakeId) => {
      voteForTake(entry.id, takeId);
    },
    [entry.id, voteForTake],
  );

  if (takes.length <= 1 || !activeTake) {
    return (
      <AudioPlayer
        audioId={entry.id}
        src={entry.assets.mp3 ?? ""}
        title={entry.title}
        entry={entry}
      />
    );
  }

  return (
    <div className="flex flex-col gap-3">
      <div
        className="flex flex-wrap gap-2"
        role="tablist"
        aria-label="Sound takes"
      >
        {takes.map((take) => {
          const selected = take.id === selectedId;
          const count = votes[take.id] ?? 0;
          const isLeader = take.id === votedDefaultId && count > 0;
          return (
            <div
              key={take.id}
              className={cn(
                "flex items-center gap-0.5 rounded-lg border px-1 py-0.5 transition-colors",
                selected ? "border-violet-500/40 bg-violet-500/5" : "border-zinc-800 bg-zinc-950/30",
              )}
            >
              <button
                type="button"
                role="tab"
                aria-selected={selected}
                title={
                  take.id === "opus"
                    ? "Claude Opus 5.5 catalog default"
                    : `Codex take ${take.label}`
                }
                onClick={() => {
                  userPicked.current = true;
                  setSelectedId(take.id);
                }}
                className={cn(
                  "rounded-md px-2 py-1 text-xs font-medium transition-colors",
                  selected ? "text-violet-100" : "text-zinc-400 hover:text-zinc-200",
                )}
              >
                {take.label}
                {isLeader && (
                  <span className="ml-1 inline-block h-1 w-1 rounded-full bg-violet-400 align-middle" />
                )}
              </button>
              <button
                type="button"
                onClick={() => onVote(take.id)}
                className="flex items-center gap-0.5 rounded-md px-1.5 py-1 text-zinc-500 transition-colors hover:bg-zinc-800/80 hover:text-violet-300"
                title={`Upvote take ${take.label}`}
                aria-label={`Upvote take ${take.label}, ${count} votes`}
              >
                <ThumbsUp className="h-3.5 w-3.5 shrink-0" aria-hidden />
                <span className="text-[10px] tabular-nums">{count}</span>
              </button>
            </div>
          );
        })}
      </div>

      <ModelBadge entry={playbackEntry} prominent />

      <AudioPlayer
        key={activeTake.id}
        audioId={`${entry.id}:${activeTake.id}`}
        src={activeTake.mp3}
        title={`${entry.title} (${activeTake.label})`}
        entry={playbackEntry}
      />
    </div>
  );
}
