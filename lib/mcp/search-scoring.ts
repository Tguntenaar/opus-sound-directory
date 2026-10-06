import type { SoundEntry } from "../entries-types";

const WEIGHT = {
  categoryExact: 10_000,
  slugExact: 9_000,
  idPrefix: 8_000,
  slugPrefix: 7_500,
  categoryToken: 7_000,
  tagWholeWord: 5_000,
  titleWholeWord: 3_000,
  titleSubstring: 800,
  descriptionWholeWord: 500,
  descriptionSubstring: 100,
  moodWholeWord: 400,
} as const;

function normalizeQuery(query: string): string {
  return query.trim().toLowerCase();
}

function queryTokens(query: string): string[] {
  return normalizeQuery(query)
    .split(/\s+/)
    .map((t) => t.trim())
    .filter(Boolean);
}

function fieldTokens(text: string): string[] {
  return text
    .toLowerCase()
    .split(/[^a-z0-9]+/)
    .filter(Boolean);
}

function hasWholeWord(text: string, token: string): boolean {
  if (!token) return false;
  return fieldTokens(text).includes(token);
}

function categoryTokens(categoryId: string): string[] {
  return categoryId.toLowerCase().split("-").filter(Boolean);
}

function scoreTokenAgainstEntry(entry: SoundEntry, token: string): number {
  if (!token) return 0;
  let score = 0;
  const category = entry.category.toLowerCase();
  const id = entry.id.toLowerCase();
  const slug = entry.slug.toLowerCase();

  if (category === token) score += WEIGHT.categoryExact;
  if (slug === token) score += WEIGHT.slugExact;
  if (id.startsWith(token)) score += WEIGHT.idPrefix;
  if (slug.startsWith(token)) score += WEIGHT.slugPrefix;
  if (categoryTokens(category).includes(token)) score += WEIGHT.categoryToken;

  for (const tag of entry.tags ?? []) {
    if (hasWholeWord(tag, token)) score += WEIGHT.tagWholeWord;
  }
  for (const mood of entry.mood ?? []) {
    if (hasWholeWord(mood, token)) score += WEIGHT.moodWholeWord;
  }

  if (hasWholeWord(entry.title, token)) score += WEIGHT.titleWholeWord;
  else if (entry.title.toLowerCase().includes(token)) score += WEIGHT.titleSubstring;

  const description = entry.prompt ?? "";
  if (hasWholeWord(description, token)) score += WEIGHT.descriptionWholeWord;
  else if (description.toLowerCase().includes(token)) score += WEIGHT.descriptionSubstring;

  return score;
}

/** Exported for unit tests and MCP ranking. */
export function scoreEntry(
  entry: SoundEntry,
  query: string,
  filters: {
    category?: string;
    mood?: string;
    tempo?: string;
    maxDurationSec?: number;
  },
): number {
  if (filters.category && entry.category !== filters.category) return -1;
  if (filters.mood && !entry.mood.includes(filters.mood)) return -1;
  if (filters.tempo && entry.tempo !== filters.tempo) return -1;
  const dur = entry.metrics.durationSec ?? entry.timing.durationSec;
  if (filters.maxDurationSec != null && dur > filters.maxDurationSec) return -1;

  const tokens = queryTokens(query);
  if (tokens.length === 0) return 1;

  let score = 0;
  for (const token of tokens) {
    score += scoreTokenAgainstEntry(entry, token);
  }
  return score;
}
