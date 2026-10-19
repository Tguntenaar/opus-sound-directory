/** Public site origin for canonical URLs, OG, sitemap, and robots. */
export function getSiteUrl(): string {
  const raw =
    process.env.SITE_URL?.trim() ||
    process.env.NEXT_PUBLIC_SITE_URL?.trim() ||
    "https://opussounds.directory";
  return raw.replace(/\/$/, "");
}

export function canonicalForPath(path: string): string {
  const base = getSiteUrl();
  if (!path || path === "/") return base;
  return `${base}${path.startsWith("/") ? path : `/${path}`}`;
}

export const SITE_NAME = "Opus Sounds Directory";

export const DEFAULT_SITE_DESCRIPTION =
  "Royalty-free sound effects and music beds for AI video, with synthesis prompts, Python code, and loudness metrics on every CC0 entry.";

export const DEFAULT_OG_IMAGE = "/og-default.png";
