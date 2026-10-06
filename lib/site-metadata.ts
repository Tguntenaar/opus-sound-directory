import type { Metadata } from "next";
import { CATEGORIES } from "@/lib/categories";
import {
  DEFAULT_OG_IMAGE,
  DEFAULT_SITE_DESCRIPTION,
  SITE_NAME,
  getSiteUrl,
} from "@/lib/site-url";

export function canonicalForPath(path: string): string {
  const base = getSiteUrl();
  if (!path || path === "/") return base;
  return `${base}${path.startsWith("/") ? path : `/${path}`}`;
}

export function rootSiteMetadata(): Metadata {
  const siteUrl = getSiteUrl();
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
        { url: "/favicon.svg", type: "image/svg+xml" },
        { url: "/favicon-32.png", sizes: "32x32", type: "image/png" },
        { url: "/favicon-16.png", sizes: "16x16", type: "image/png" },
      ],
      apple: [{ url: "/apple-touch-icon.png", sizes: "180x180", type: "image/png" }],
    },
    manifest: "/site.webmanifest",
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
          alt: "Opus Sound Directory — synthesised beds and SFX",
        },
      ],
    },
    twitter: {
      card: "summary_large_image",
      title: SITE_NAME,
      description: DEFAULT_SITE_DESCRIPTION,
      images: [DEFAULT_OG_IMAGE],
    },
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
