import type { SoundEntry } from "@/lib/entries-types";
import type { StatsMap } from "@/lib/stats-types";

export type SortMode = "popular" | "new";

export function popularityScore(entryId: string, stats: StatsMap): number {
  const s = stats[entryId];
  if (!s) return 0;
  return s.copy + s.download;
}

export function sortEntries(
  entries: SoundEntry[],
  mode: SortMode,
  stats: StatsMap,
): SoundEntry[] {
  const list = [...entries];
  if (mode === "new") {
    list.sort((a, b) => b.generatedAt.localeCompare(a.generatedAt));
    return list;
  }
  list.sort((a, b) => {
    const diff = popularityScore(b.id, stats) - popularityScore(a.id, stats);
    if (diff !== 0) return diff;
    return b.generatedAt.localeCompare(a.generatedAt);
  });
  return list;
}

export function matchesSearch(entry: SoundEntry, query: string): boolean {
  const q = query.trim().toLowerCase();
  if (!q) return true;
  const hay = [
    entry.title,
    entry.category,
    ...(entry.tags ?? []),
    ...(entry.mood ?? []),
    entry.prompt.slice(0, 200),
  ]
    .join(" ")
    .toLowerCase();
  return hay.includes(q);
}
