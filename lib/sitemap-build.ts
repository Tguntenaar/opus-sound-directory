import type { MetadataRoute } from "next";
import { CATEGORY_ORDER } from "./categories.ts";
import type { SoundEntry } from "./entries-types.ts";
import type { BlogPost } from "./blog-types.ts";
import { getSiteUrl } from "./site-url.ts";

/** HTML index routes included in `/sitemap.xml` (not APIs, MCP, or feeds). */
export const SITEMAP_STATIC_PATHS = [
  "/",
  "/about",
  "/agents",
  "/sponsor",
  "/blog",
] as const;

/** Path prefixes that must never appear in the sitemap. */
export const SITEMAP_FORBIDDEN_PATH_PREFIXES = [
  "/mcp",
  "/api",
  "/audio",
  "/llms",
  "/ingest",
  "/.well-known",
] as const;

export type SitemapPageContext = {
  entrySlugs: ReadonlySet<string>;
  blogSlugs: ReadonlySet<string>;
  categories: readonly string[];
};

export function pathnameFromSitemapUrl(url: string, base: string): string {
  if (!url.startsWith(base)) {
    throw new Error(`Sitemap URL ${url} is not under base ${base}`);
  }
  const path = url.slice(base.length) || "/";
  return path.startsWith("/") ? path : `/${path}`;
}

export function isSitemapHtmlPagePath(
  pathname: string,
  ctx: SitemapPageContext,
): boolean {
  if (pathname !== "/" && pathname.endsWith("/")) {
    return false;
  }
  if ((SITEMAP_STATIC_PATHS as readonly string[]).includes(pathname)) {
    return true;
  }
  const categoryMatch = /^\/c\/([^/]+)$/.exec(pathname);
  if (categoryMatch && ctx.categories.includes(categoryMatch[1]!)) {
    return true;
  }
  const blogMatch = /^\/blog\/([^/]+)$/.exec(pathname);
  if (blogMatch && ctx.blogSlugs.has(blogMatch[1]!)) {
    return true;
  }
  const entryMatch = /^\/e\/([^/]+)$/.exec(pathname);
  if (entryMatch && ctx.entrySlugs.has(entryMatch[1]!)) {
    return true;
  }
  return false;
}

export function sitemapPageContextFromData(
  entries: readonly SoundEntry[],
  blogPosts: readonly BlogPost[],
): SitemapPageContext {
  return {
    entrySlugs: new Set(entries.map((e) => e.slug)),
    blogSlugs: new Set(blogPosts.map((p) => p.slug)),
    categories: CATEGORY_ORDER,
  };
}

export function buildSitemapFromData(
  entries: readonly SoundEntry[],
  blogPosts: readonly BlogPost[],
): MetadataRoute.Sitemap {
  const base = getSiteUrl();
  const now = new Date();

  const staticPriority = (path: (typeof SITEMAP_STATIC_PATHS)[number]): number => {
    switch (path) {
      case "/":
        return 1;
      case "/sponsor":
        return 0.9;
      case "/about":
        return 0.85;
      case "/agents":
        return 0.8;
      case "/blog":
        return 0.7;
      default:
        return 0.8;
    }
  };

  const staticPages: MetadataRoute.Sitemap = SITEMAP_STATIC_PATHS.map((path) => ({
    url: path === "/" ? base : `${base}${path}`,
    lastModified: now,
    changeFrequency: path === "/" || path === "/blog" ? "weekly" : "monthly",
    priority: staticPriority(path),
  }));

  const categoryPages: MetadataRoute.Sitemap = CATEGORY_ORDER.map((category) => ({
    url: `${base}/c/${category}`,
    lastModified: now,
    changeFrequency: "weekly" as const,
    priority: 0.88,
  }));

  const blogPostPages: MetadataRoute.Sitemap = blogPosts.map((post) => ({
    url: `${base}/blog/${post.slug}`,
    lastModified: new Date(post.date),
    changeFrequency: "monthly" as const,
    priority: 0.65,
  }));

  const entryPages: MetadataRoute.Sitemap = entries.map((entry) => ({
    url: `${base}/e/${entry.slug}`,
    lastModified: entry.generatedAt ? new Date(entry.generatedAt) : now,
    changeFrequency: "monthly" as const,
    priority: 0.8,
  }));

  return [...staticPages, ...categoryPages, ...blogPostPages, ...entryPages];
}
