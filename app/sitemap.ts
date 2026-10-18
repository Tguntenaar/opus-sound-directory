import type { MetadataRoute } from "next";
import { getAllBlogPosts } from "@/lib/blog";
import { getAllEntriesMerged } from "@/lib/entries";
import { buildSitemapFromData } from "@/lib/sitemap-build";

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const [entries, blogPosts] = await Promise.all([
    getAllEntriesMerged(),
    Promise.resolve(getAllBlogPosts()),
  ]);
  return buildSitemapFromData(entries, blogPosts);
}
