/** Public site origin for canonical URLs, OG, sitemap, and robots. */
export function getSiteUrl(): string {
  const raw =
    process.env.SITE_URL?.trim() ||
    process.env.NEXT_PUBLIC_SITE_URL?.trim() ||
    "https://opus-sound-directory.workers.dev";
  return raw.replace(/\/$/, "");
}

export const SITE_NAME = "Opus Sound Directory";

export const DEFAULT_SITE_DESCRIPTION =
  "Browsable directory of Claude Opus–generated synthesised audio: prompts, Python code, spectrograms, and measured loudness for video beds and SFX.";

export const DEFAULT_OG_IMAGE = "/og-default.png";
