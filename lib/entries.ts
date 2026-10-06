import { ALL_ENTRIES } from "./entries.generated";
import type { SoundEntry } from "./entries-types";

export type { SoundEntry } from "./entries-types";

export function getAllEntries(): SoundEntry[] {
  return [...ALL_ENTRIES].sort((a, b) => a.title.localeCompare(b.title));
}

export function getEntryBySlug(slug: string): SoundEntry | undefined {
  return ALL_ENTRIES.find((e) => e.slug === slug);
}

export function getEntryById(id: string): SoundEntry | undefined {
  return ALL_ENTRIES.find((e) => e.id === id);
}

export function getEntriesByCategory(category: string): SoundEntry[] {
  return getAllEntries().filter((e) => e.category === category);
}
