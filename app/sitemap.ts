import type { MetadataRoute } from "next";
import { getAllEntries } from "@/lib/entries";
import { getSiteUrl } from "@/lib/site-url";

export default function sitemap(): MetadataRoute.Sitemap {
  const base = getSiteUrl();
  const now = new Date();
  const entries = getAllEntries();

  const staticPages: MetadataRoute.Sitemap = [
    {
      url: base,
      lastModified: now,
      changeFrequency: "weekly",
      priority: 1,
    },
    {
      url: `${base}/sponsor`,
      lastModified: now,
      changeFrequency: "monthly",
      priority: 0.9,
    },
  ];

  const entryPages: MetadataRoute.Sitemap = entries.map((entry) => ({
    url: `${base}/e/${entry.slug}`,
    lastModified: entry.generatedAt ? new Date(entry.generatedAt) : now,
    changeFrequency: "monthly" as const,
    priority: 0.8,
  }));

  return [...staticPages, ...entryPages];
}
