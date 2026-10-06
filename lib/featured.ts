import type { SoundEntry } from "@/lib/entries-types";

/** Editorial featured pick on the home grid when `content/sponsors.json` home is null. */
export const FEATURED_ENTRY_SLUG = "chaos-calm-01";

export function getFeaturedEntry(entries: SoundEntry[]): SoundEntry | null {
  if (entries.length === 0) return null;
  return entries.find((e) => e.slug === FEATURED_ENTRY_SLUG) ?? entries[0];
}
