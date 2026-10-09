"use client";

import { Layers } from "lucide-react";
import type { SoundEntry } from "@/lib/entries";
import { entryTakesFor } from "@/lib/hero8-takes";

export function EntryTakeAffordance({ entry }: { entry: SoundEntry }) {
  const takes = entryTakesFor(entry);
  if (takes.length <= 1) return null;
  return (
    <span
      className="inline-flex items-center text-zinc-500"
      title={`${takes.length} takes — compare on detail page`}
    >
      <Layers className="h-3.5 w-3.5" aria-hidden />
      <span className="sr-only">{takes.length} alternate takes</span>
    </span>
  );
}
