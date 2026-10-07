import type { Metadata } from "next";
import { CATEGORIES } from "@/lib/categories";
import {
  DEFAULT_OG_IMAGE,
  DEFAULT_SITE_DESCRIPTION,
  SITE_NAME,
  getSiteUrl,
} from "@/lib/site-url";

/** Bump when favicon assets change so browsers pick up new icons. */
export const FAVICON_VERSION = "2";

function iconHref(path: string): string {
  return `${path}?v=${FAVICON_VERSION}`;
}

export function canonicalForPath(path: string): string {
  const base = getSiteUrl();
  if (!path || path === "/") return base;
  return `${base}${path.startsWith("/") ? path : `/${path}`}`;
}

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
  const googleVerification = process.env.GOOGLE_SITE_VERIFICATION?.trim();
  const bingVerification = process.env.BING_SITE_VERIFICATION?.trim();
  return {
    metadataBase: new URL(siteUrl),
    title: {
      default: SITE_NAME,
      template: `%s · ${SITE_NAME}`,
    },
    description: DEFAULT_SITE_DESCRIPTION,
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
      description: DEFAULT_SITE_DESCRIPTION,
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
      description: DEFAULT_SITE_DESCRIPTION,
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
