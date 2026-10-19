import type { Metadata } from "next";
import { CATEGORIES } from "./categories.ts";
import {
  DEFAULT_OG_IMAGE,
  DEFAULT_SITE_DESCRIPTION,
  SITE_NAME,
  canonicalForPath,
  getSiteUrl,
} from "./site-url.ts";
import { fitMetaDescription } from "./seo-limits.ts";

/** Bump when favicon assets change so browsers pick up new icons. */
export const FAVICON_VERSION = "2";

function iconHref(path: string): string {
  return `${path}?v=${FAVICON_VERSION}`;
}

export { canonicalForPath } from "./site-url.ts";

/** Canonical + RSS discovery for `/blog` and `/blog/<slug>` pages. */
export function blogPageAlternates(canonicalPath: string): Metadata["alternates"] {
  return {
    canonical: canonicalForPath(canonicalPath),
    types: {
      "application/rss+xml": canonicalForPath("/blog/rss.xml"),
    },
  };
}

export function rootSiteMetadata(): Metadata {
  const siteUrl = getSiteUrl();
  const siteDescription = fitMetaDescription(DEFAULT_SITE_DESCRIPTION);
  const googleVerification = process.env.GOOGLE_SITE_VERIFICATION?.trim();
  const bingVerification = process.env.BING_SITE_VERIFICATION?.trim();
  return {
    metadataBase: new URL(siteUrl),
    title: {
      default: "Free CC0 Sound Effects & Music Beds",
      template: `%s · ${SITE_NAME}`,
    },
    description: siteDescription,
    alternates: {
      canonical: siteUrl,
    },
    icons: {
      icon: [
        { url: iconHref("/favicon.ico"), sizes: "any" },
        { url: iconHref("/favicon.svg"), type: "image/svg+xml" },
        { url: iconHref("/favicon-48.png"), sizes: "48x48", type: "image/png" },
        { url: iconHref("/favicon-32.png"), sizes: "32x32", type: "image/png" },
        { url: iconHref("/favicon-16.png"), sizes: "16x16", type: "image/png" },
      ],
      apple: [{ url: iconHref("/apple-touch-icon.png"), sizes: "180x180", type: "image/png" }],
    },
    manifest: iconHref("/site.webmanifest"),
    openGraph: {
      type: "website",
      locale: "en_US",
      url: siteUrl,
      siteName: SITE_NAME,
      title: SITE_NAME,
      description: siteDescription,
      images: [
        {
          url: DEFAULT_OG_IMAGE,
          width: 1200,
          height: 630,
          alt: "Opus Sounds Directory — synthesised beds and SFX",
        },
      ],
    },
    twitter: {
      card: "summary_large_image",
      title: SITE_NAME,
      description: siteDescription,
      images: [DEFAULT_OG_IMAGE],
    },
    ...(googleVerification || bingVerification
      ? {
          verification: {
            ...(googleVerification ? { google: googleVerification } : {}),
            ...(bingVerification
              ? { other: { "msvalidate.01": bingVerification } }
              : {}),
          },
        }
      : {}),
  };
}

export function entryShareDescription(entry: {
  title: string;
  category: string;
  timing: { durationSec: number };
  metrics: { lufs: number };
}): string {
  const dur = entry.timing.durationSec;
  const lufs = entry.metrics.lufs;
  const cat = CATEGORIES[entry.category as keyof typeof CATEGORIES]?.label ?? entry.category;
  return `${entry.title} — ${cat}, ${dur}s, ${lufs} LUFS integrated. Prompt, code, spectrogram, and downloads.`;
}
