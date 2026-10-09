import type { SoundEntry } from "@/lib/entries-types";

/** Editorial featured pick on the home grid when `content/sponsors.json` home is null. */
export const FEATURED_ENTRY_SLUG = "endless-riser-shepard";
export const FEATURED_CONTROL_SLUG = "chaos-calm-01";
export const FEATURED_EXPERIMENT_FLAG = "homepage-featured-sound-v1";

export function featuredVariant(value: unknown): "control" | "endless-riser" | null {
  return value === "control" || value === "endless-riser" ? value : null;
}

export function getFeaturedEntry(entries: SoundEntry[]): SoundEntry | null {
  if (entries.length === 0) return null;
  return entries.find((e) => e.slug === FEATURED_ENTRY_SLUG) ?? entries[0];
}
