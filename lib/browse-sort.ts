import type { SoundEntry } from "@/lib/entries-types";
import type { StatsMap } from "@/lib/stats-types";

export type SortMode = "popular" | "new";

/** Tie-break when popularity scores match (typical cold start). Lower index = earlier in grid. */
export const EDITORIAL_COLD_START_ORDER: readonly string[] = [
  "heavy-boom-meme",
  "whoosh-pass-by",
  "ui-cozy-sprite",
  "endless-riser-shepard",
  "dialup-modem-56k",
  "arcade-game-over",
  "trailer-braam-hit",
  "drop-impact-heavy",
  "wah-wah-fail",
  "drop-whoosh-stinger",
  "ui-success-chime",
  "ui-toggle-on",
  "logo-sting-bright",
];

const editorialTieRank = (() => {
  const rank = new Map<string, number>();
  EDITORIAL_COLD_START_ORDER.forEach((id, i) => rank.set(id, i));
  const fallback = EDITORIAL_COLD_START_ORDER.length;
  return (id: string) => rank.get(id) ?? fallback;
})();

export function popularityScore(entryId: string, stats: StatsMap): number {
  const s = stats[entryId];
  if (!s) return 0;
  // Reuse intent outweighs listening; old counters without plays remain valid.
  return (s.play ?? 0) + 3 * (s.copy ?? 0) + 5 * (s.download ?? 0);
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
    const rankDiff = editorialTieRank(a.id) - editorialTieRank(b.id);
    if (rankDiff !== 0) return rankDiff;
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
