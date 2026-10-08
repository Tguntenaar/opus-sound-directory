import { listCommunityEntries, getCommunityEntryBySlug } from "./community-kv";
import { ALL_ENTRIES } from "./entries.generated";
import type { SoundEntry } from "./entries-types";
import { isEntryHidden } from "./entry-visibility";

export type { SoundEntry } from "./entries-types";
export { isEntryHidden } from "./entry-visibility";

export function getAllEntries(): SoundEntry[] {
  return [...ALL_ENTRIES]
    .filter((e) => !isEntryHidden(e))
    .sort((a, b) => a.title.localeCompare(b.title));
}

export async function getAllEntriesMerged(): Promise<SoundEntry[]> {
  const community = await listCommunityEntries();
  return [...getAllEntries(), ...community].sort((a, b) =>
    a.title.localeCompare(b.title),
  );
}

function findStaticEntry(
  predicate: (e: SoundEntry) => boolean,
  includeHidden = false,
): SoundEntry | undefined {
  const entry = ALL_ENTRIES.find(predicate);
  if (!entry) return undefined;
  if (isEntryHidden(entry) && !includeHidden) return undefined;
  return entry;
}

export function getEntryBySlug(slug: string, includeHidden = false): SoundEntry | undefined {
  return findStaticEntry((e) => e.slug === slug, includeHidden);
}

export async function getEntryBySlugMerged(
  slug: string,
  includeHidden = false,
): Promise<SoundEntry | undefined> {
  const staticEntry = getEntryBySlug(slug, includeHidden);
  if (staticEntry) return staticEntry;
  return (await getCommunityEntryBySlug(slug)) ?? undefined;
}

export function getEntryById(id: string, includeHidden = false): SoundEntry | undefined {
  return findStaticEntry((e) => e.id === id, includeHidden);
}

export function getEntriesByCategory(category: string): SoundEntry[] {
  return getAllEntries().filter((e) => e.category === category);
}
