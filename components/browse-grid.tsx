"use client";

import { useMemo, useState } from "react";
import type { SoundEntry } from "@/lib/entries";
import { CATEGORY_ORDER, CATEGORIES } from "@/lib/categories";
import { MOOD_FACETS, formatMood } from "@/lib/mood";
import { EntryCard } from "@/components/entry-card";
import { cn } from "@/lib/utils";

type Props = {
  entries: SoundEntry[];
};

function moodsInCatalog(entries: SoundEntry[]): string[] {
  const set = new Set<string>();
  for (const e of entries) {
    for (const m of e.mood ?? []) set.add(m);
  }
  return Object.keys(MOOD_FACETS).filter((k) => set.has(k));
}

export function BrowseGrid({ entries }: Props) {
  const [category, setCategory] = useState<string | "all">("all");
  const [mood, setMood] = useState<string | "all">("all");

  const moodOptions = useMemo(() => moodsInCatalog(entries), [entries]);

  const filtered = useMemo(() => {
    return entries.filter((e) => {
      if (category !== "all" && e.category !== category) return false;
      if (mood !== "all" && !(e.mood ?? []).includes(mood)) return false;
      return true;
    });
  }, [entries, category, mood]);

  const chip =
    "rounded-full px-3 py-1 text-xs transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-violet-500/60";
  const chipIdle = "text-zinc-500 hover:text-zinc-300";
  const chipActive = "bg-violet-500/15 text-violet-200";

  return (
    <div className="flex flex-col gap-8">
      <div className="flex flex-col gap-4">
        <div className="flex flex-wrap gap-1.5" role="group" aria-label="Category">
          <button
            type="button"
            onClick={() => setCategory("all")}
            className={cn(chip, category === "all" ? chipActive : chipIdle)}
          >
            All
          </button>
          {CATEGORY_ORDER.map((id) => {
            const count = entries.filter((e) => e.category === id).length;
            if (count === 0) return null;
            const active = category === id;
            return (
              <button
                key={id}
                type="button"
                onClick={() => setCategory(id)}
                className={cn(chip, active ? chipActive : chipIdle)}
              >
                {CATEGORIES[id].label}
              </button>
            );
          })}
        </div>
        {moodOptions.length > 0 && (
          <div className="flex flex-wrap gap-1.5" role="group" aria-label="Mood">
            <button
              type="button"
              onClick={() => setMood("all")}
              className={cn(chip, mood === "all" ? chipActive : chipIdle)}
            >
              Any mood
            </button>
            {moodOptions.map((id) => (
              <button
                key={id}
                type="button"
                onClick={() => setMood(id)}
                className={cn(chip, mood === id ? chipActive : chipIdle)}
              >
                {formatMood(id)}
              </button>
            ))}
          </div>
        )}
      </div>

      {filtered.length === 0 ? (
        <p className="py-16 text-center text-sm text-zinc-600">No sounds match these filters.</p>
      ) : (
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((entry) => (
            <EntryCard key={entry.id} entry={entry} />
          ))}
        </div>
      )}
    </div>
  );
}
