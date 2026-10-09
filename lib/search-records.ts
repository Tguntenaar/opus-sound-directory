import type { SoundEntry } from "./entries-types.ts";

export type SearchRecord = {
  objectID: string;
  id: string;
  modelId: string;
  previewUrl: string | null;
  slug: string;
  title: string;
  category: string;
  tags: string[];
  mood: string[];
  description: string;
  durationSec: number;
};

/** Keep search records small and include only public catalog fields. */
export function toSearchRecords(entries: SoundEntry[]): SearchRecord[] {
  return entries.filter((entry) => !entry.hidden).map((entry) => ({
    objectID: entry.slug,
    id: entry.id,
    modelId: entry.modelId,
    previewUrl: entry.hasRenderedAudio === false ? null : entry.assets.mp3 || entry.assets.wav || null,
    slug: entry.slug,
    title: entry.title,
    category: entry.category,
    tags: entry.tags ?? [],
    mood: entry.mood ?? [],
    description: entry.prompt.slice(0, 1500),
    durationSec: entry.timing.durationSec,
  }));
}

export type SearchResults = {
  hits: SearchRecord[];
  nbHits: number;
  provider: "algolia" | "catalog";
};

export function searchCatalog(records: SearchRecord[], query: string): SearchResults {
  const terms = query.toLowerCase().split(/\s+/).filter(Boolean);
  const hits = records.filter((record) => {
    const text = [record.title, record.category, ...record.tags, ...record.mood, record.description].join(" ").toLowerCase();
    return terms.every((term) => text.includes(term));
  }).sort((a, b) => Number(b.title.toLowerCase().includes(query.toLowerCase())) - Number(a.title.toLowerCase().includes(query.toLowerCase())));
  return { hits: hits.slice(0, 12), nbHits: hits.length, provider: "catalog" };
}
