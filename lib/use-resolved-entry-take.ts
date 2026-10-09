"use client";

import { useMemo } from "react";
import type { SoundEntry } from "@/lib/entries";
import { entryTakesFor } from "@/lib/hero8-takes";
import { pickDefaultTake } from "@/lib/take-selection";
import { useTakeVotes } from "@/components/take-votes-provider";

export function useResolvedEntryTake(entry: SoundEntry) {
  const takes = useMemo(() => entryTakesFor(entry), [entry]);
  const { getVotes } = useTakeVotes();
  const votes = getVotes(entry.id);

  const defaultTake = useMemo(
    () => (takes.length ? pickDefaultTake(takes, votes) : null),
    [takes, votes],
  );

  return { takes, votes, defaultTake, hasTakes: takes.length > 1 };
}
