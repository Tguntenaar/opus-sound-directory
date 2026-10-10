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

function catalogSearchText(record: SearchRecord): string {
  return [record.slug, record.id, record.title, record.category, ...record.tags, ...record.mood, record.description].join(" ").toLowerCase();
}

/** All public catalog records matching the query, best title matches first. */
export function matchCatalogRecords(records: SearchRecord[], query: string): SearchRecord[] {
  const terms = query.toLowerCase().split(/\s+/).filter(Boolean);
  const needle = query.toLowerCase();
  return records.filter((record) => {
    const text = catalogSearchText(record);
    return terms.every((term) => text.includes(term));
  }).sort((a, b) => Number(b.title.toLowerCase().includes(needle)) - Number(a.title.toLowerCase().includes(needle)));
}

export function searchCatalog(records: SearchRecord[], query: string): SearchResults {
  const matches = matchCatalogRecords(records, query);
  return { hits: matches.slice(0, 12), nbHits: matches.length, provider: "catalog" };
}

/** Algolia first, then catalog-only hits so deployed sounds appear when the index is stale. */
export function mergeAlgoliaWithCatalog(
  algoliaHits: SearchRecord[],
  algoliaNbHits: number,
  catalogMatches: SearchRecord[],
  limit = 12,
): SearchResults {
  const seen = new Set<string>();
  const hits: SearchRecord[] = [];
  for (const hit of algoliaHits) {
    const key = hit.objectID || hit.slug;
    if (seen.has(key)) continue;
    seen.add(key);
    hits.push(hit);
  }
  for (const hit of catalogMatches) {
    const key = hit.objectID || hit.slug;
    if (seen.has(key)) continue;
    seen.add(key);
    hits.push(hit);
    if (hits.length >= limit) break;
  }
  return {
    hits: hits.slice(0, limit),
    nbHits: Math.max(algoliaNbHits, catalogMatches.length),
    provider: "algolia",
  };
}
