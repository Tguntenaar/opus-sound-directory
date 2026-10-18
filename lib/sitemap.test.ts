import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { describe, it } from "node:test";
import { ALL_BLOG_POSTS } from "./blog.generated.ts";
import type { BlogPost } from "./blog-types.ts";
import { CATEGORY_ORDER } from "./categories.ts";
import type { SoundEntry } from "./entries-types.ts";
import { isEntryHidden } from "./entry-visibility.ts";
import {
  SITEMAP_FORBIDDEN_PATH_PREFIXES,
  buildSitemapFromData,
  isSitemapHtmlPagePath,
  pathnameFromSitemapUrl,
  sitemapPageContextFromData,
} from "./sitemap-build.ts";
import { getSiteUrl } from "./site-url.ts";

const entriesDir = path.join(import.meta.dirname, "../content/entries");

function catalogEntriesForSitemap(): SoundEntry[] {
  return fs
    .readdirSync(entriesDir)
    .filter((f) => f.endsWith(".json"))
    .map(
      (f) =>
        JSON.parse(fs.readFileSync(path.join(entriesDir, f), "utf8")) as SoundEntry,
    )
    .filter((e) => !isEntryHidden(e))
    .sort((a, b) => a.title.localeCompare(b.title));
}

function blogPostsForSitemap(): BlogPost[] {
  return ALL_BLOG_POSTS.filter((p) => !p.draft).sort((a, b) =>
    b.date.localeCompare(a.date),
  );
}

describe("sitemap", () => {
  it("lists only crawlable HTML page routes", () => {
    const base = getSiteUrl();
    const entries = catalogEntriesForSitemap();
    const blogPosts = blogPostsForSitemap();
    const rows = buildSitemapFromData(entries, blogPosts);
    const ctx = sitemapPageContextFromData(entries, blogPosts);

    assert.ok(rows.length > 0, "sitemap should not be empty");

    for (const row of rows) {
      const pathname = pathnameFromSitemapUrl(row.url, base);

      for (const prefix of SITEMAP_FORBIDDEN_PATH_PREFIXES) {
        assert.ok(
          !pathname.startsWith(prefix),
          `sitemap must not include non-page path ${pathname} (forbidden prefix ${prefix})`,
        );
      }

      assert.ok(
        isSitemapHtmlPagePath(pathname, ctx),
        `sitemap URL ${row.url} does not map to a page route`,
      );
    }
  });

  it("does not include the MCP streamable-http endpoint", () => {
    const base = getSiteUrl();
    const rows = buildSitemapFromData(
      catalogEntriesForSitemap(),
      blogPostsForSitemap(),
    );
    const mcpUrls = rows.filter((row) => row.url === `${base}/mcp`);
    assert.equal(mcpUrls.length, 0);
  });

  it("covers every published blog post and catalog entry slug", () => {
    const base = getSiteUrl();
    const entries = catalogEntriesForSitemap();
    const blogPosts = blogPostsForSitemap();
    const rows = buildSitemapFromData(entries, blogPosts);
    const paths = new Set(rows.map((row) => pathnameFromSitemapUrl(row.url, base)));

    for (const post of blogPosts) {
      assert.ok(paths.has(`/blog/${post.slug}`), `missing blog post ${post.slug}`);
    }

    for (const entry of entries) {
      assert.ok(paths.has(`/e/${entry.slug}`), `missing entry ${entry.slug}`);
    }

    for (const category of CATEGORY_ORDER) {
      assert.ok(paths.has(`/c/${category}`), `missing category ${category}`);
    }
  });
});
