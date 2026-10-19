import { SITE_NAME } from "./site-url.ts";

/** Match scripts/crawl-audit.mjs snippet limits. */
export const TITLE_MIN = 30;
export const TITLE_MAX = 65;
export const DESC_MIN = 70;
export const DESC_MAX = 160;

const TITLE_SUFFIX_SEP = " · ";

export function titleSuffix(siteName = SITE_NAME): string {
  return `${TITLE_SUFFIX_SEP}${siteName}`;
}

/** Full `<title>` as rendered with the root metadata template. */
export function documentTitleFromSegment(segment: string, siteName = SITE_NAME): string {
  return `${segment}${titleSuffix(siteName)}`;
}

export function maxTitleSegmentLength(siteName = SITE_NAME): number {
  return TITLE_MAX - titleSuffix(siteName).length;
}

/** True when text was shortened with an ellipsis marker (Unicode or ASCII). */
export function endsWithTruncationEllipsis(text: string): boolean {
  const t = text.trimEnd();
  return t.endsWith("…") || t.endsWith("...");
}

export function truncateAtWordBoundary(text: string, maxLen: number, ellipsis = "…"): string {
  const trimmed = text.trim();
  if (trimmed.length <= maxLen) return trimmed;
  const room = maxLen - ellipsis.length;
  if (room <= 0) return ellipsis.slice(0, maxLen);
  let cut = trimmed.slice(0, room);
  const lastSpace = cut.lastIndexOf(" ");
  if (lastSpace > Math.floor(room * 0.45)) {
    cut = cut.slice(0, lastSpace);
  }
  return cut.trimEnd() + ellipsis;
}

/** First variant whose full document title fits; otherwise truncate the last variant's segment. */
export function pickTitleSegment(variants: string[], siteName = SITE_NAME): string {
  const maxSeg = maxTitleSegmentLength(siteName);
  for (const segment of variants) {
    if (segment.length <= maxSeg) return segment;
  }
  const fallback = variants[variants.length - 1] ?? "";
  return truncateAtWordBoundary(fallback, maxSeg);
}

export function fitMetaDescription(description: string): string {
  const trimmed = description.trim();
  if (trimmed.length <= DESC_MAX) return trimmed;
  return truncateAtWordBoundary(trimmed, DESC_MAX);
}

/** First meta description variant within DESC_MAX; truncate last if needed. */
export function pickMetaDescription(variants: string[]): string {
  for (const desc of variants) {
    const trimmed = desc.trim();
    if (trimmed.length <= DESC_MAX) return trimmed;
  }
  const fallback = variants[variants.length - 1] ?? "";
  return fitMetaDescription(fallback);
}
