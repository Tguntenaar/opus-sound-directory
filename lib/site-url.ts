/** Public site origin for canonical URLs, OG, sitemap, and robots. */
export function getSiteUrl(): string {
  const raw =
    process.env.SITE_URL?.trim() ||
    process.env.NEXT_PUBLIC_SITE_URL?.trim() ||
    "https://opussounds.directory";
  return raw.replace(/\/$/, "");
}

export const SITE_NAME = "Opus Sounds Directory";

export const DEFAULT_SITE_DESCRIPTION =
  "Royalty-free sound effects and music beds for AI videos, each with the prompt, Python synth code and loudness metrics behind it.";

export const DEFAULT_OG_IMAGE = "/og-default.png";
