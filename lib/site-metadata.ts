import type { Metadata } from "next";
import { CATEGORIES } from "@/lib/categories";
import {
  DEFAULT_OG_IMAGE,
  DEFAULT_SITE_DESCRIPTION,
  SITE_NAME,
  getSiteUrl,
} from "@/lib/site-url";

export function rootSiteMetadata(): Metadata {
  const siteUrl = getSiteUrl();
  return {
    metadataBase: new URL(siteUrl),
    title: {
      default: SITE_NAME,
      template: `%s · ${SITE_NAME}`,
    },
    description: DEFAULT_SITE_DESCRIPTION,
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
