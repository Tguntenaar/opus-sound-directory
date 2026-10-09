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

/**
 * Everyday search words → words the catalog actually uses. Short UI sounds are
 * described by what they are ("chime", "toggle"), not by what people search
 * for ("notification", "button"), so literal matching alone misses them.
 * Related terms are discounted (nouns more than adjectives) and a matching
 * category adds a small flat boost, so no single related word outweighs a
 * literal tag or title match.
 */
type RelatedGroup = {
  queries: string[];
  related: string[];
  category?: string;
  factor: number;
};

const RELATED_GROUPS: RelatedGroup[] = [
  {
    queries: ["notification", "notify", "alert", "ping", "ding", "beep", "chime", "bell"],
    related: ["chime", "ping", "ding", "message", "notification"],
    category: "ui-sounds",
    factor: 0.5,
  },
  {
    queries: ["click", "tap", "button", "toggle", "switch", "press"],
    related: ["toggle", "tap", "click", "switch", "tactile"],
    category: "ui-sounds",
    factor: 0.5,
  },
  {
    queries: ["success", "confirm", "confirmation", "complete", "done", "correct"],
    related: ["success", "chime"],
    category: "ui-sounds",
    factor: 0.5,
  },
  {
    queries: ["error", "fail", "failure", "wrong", "denied", "invalid", "nope", "warning"],
    related: ["error", "fail", "nope"],
    category: "ui-sounds",
    factor: 0.5,
  },
  {
    queries: ["send", "sent", "message", "chat", "sms"],
    related: ["message", "send", "swish"],
    category: "ui-sounds",
    factor: 0.5,
  },
  {
    queries: ["coin", "pickup", "collect", "collectible", "reward", "points"],
    related: ["coin", "pickup", "collect", "sparkle"],
    factor: 0.5,
  },
  {
    queries: ["gentle", "soft", "subtle", "quiet", "calm"],
    related: ["gentle", "soft", "subtle", "calm"],
    factor: 0.15,
  },
];

const CATEGORY_HINT = 2_000;

/** The token plus a naive singular form ("notifications" → "notification"). */
function tokenVariants(token: string): string[] {
  const variants = [token];
  if (token.length > 4 && token.endsWith("ies")) variants.push(`${token.slice(0, -3)}y`);
  else if (/(s|x|ch|sh)es$/.test(token)) variants.push(token.slice(0, -2));
  else if (token.length > 3 && token.endsWith("s") && !token.endsWith("ss")) {
    variants.push(token.slice(0, -1));
  }
  return variants;
}

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

/** `wholeWordsOnly` skips id/slug prefix rules, so related term "tap" can't hit "tape-stop". */
function scoreTokenAgainstEntry(
  entry: SoundEntry,
  token: string,
  wholeWordsOnly = false,
): number {
  if (!token) return 0;
  let score = 0;
  const category = entry.category.toLowerCase();
  const id = entry.id.toLowerCase();
  const slug = entry.slug.toLowerCase();

  if (category === token) score += WEIGHT.categoryExact;
  if (slug === token) score += WEIGHT.slugExact;
  if (!wholeWordsOnly && id.startsWith(token)) score += WEIGHT.idPrefix;
  if (!wholeWordsOnly && slug.startsWith(token)) score += WEIGHT.slugPrefix;
  if (categoryTokens(category).includes(token)) score += WEIGHT.categoryToken;

  for (const tag of entry.tags ?? []) {
    if (hasWholeWord(tag, token)) score += WEIGHT.tagWholeWord;
  }
  for (const mood of entry.mood ?? []) {
    if (hasWholeWord(mood, token)) score += WEIGHT.moodWholeWord;
  }

  if (hasWholeWord(entry.title, token)) score += WEIGHT.titleWholeWord;
  else if (!wholeWordsOnly && entry.title.toLowerCase().includes(token)) {
    score += WEIGHT.titleSubstring;
  }

  const description = entry.prompt ?? "";
  if (hasWholeWord(description, token)) score += WEIGHT.descriptionWholeWord;
  else if (!wholeWordsOnly && description.toLowerCase().includes(token)) {
    score += WEIGHT.descriptionSubstring;
  }

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
    const variants = tokenVariants(token);
    score += Math.max(...variants.map((v) => scoreTokenAgainstEntry(entry, v)));

    for (const group of RELATED_GROUPS) {
      if (!variants.some((v) => group.queries.includes(v))) continue;
      let relatedScore = 0;
      for (const term of group.related) {
        if (!variants.includes(term)) relatedScore += scoreTokenAgainstEntry(entry, term, true);
      }
      score += Math.round(relatedScore * group.factor);
      if (group.category === entry.category) score += CATEGORY_HINT;
    }
  }
  return score;
}
