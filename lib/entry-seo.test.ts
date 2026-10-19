import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { describe, it } from "node:test";
import type { SoundEntry } from "./entries-types.ts";
import { isEntryHidden } from "./entry-visibility.ts";
import { entryMetaDescription, entryPageTitle } from "./entry-seo.ts";
import { blogPageTitle } from "./blog-seo.ts";
import { CATEGORY_SEO } from "./category-seo.ts";
import { categoryPageDescription, categoryPageTitle } from "./category-seo-meta.ts";
import {
  DESC_MAX,
  DESC_MIN,
  TITLE_MAX,
  documentTitleFromSegment,
  endsWithTruncationEllipsis,
  fitMetaDescription,
} from "./seo-limits.ts";
import { SITE_NAME, DEFAULT_SITE_DESCRIPTION } from "./site-url.ts";
import { ALL_BLOG_POSTS } from "./blog.generated.ts";

const entriesDir = path.join(import.meta.dirname, "../content/entries");

function loadPublicCatalog(): SoundEntry[] {
  return fs
    .readdirSync(entriesDir)
    .filter((f) => f.endsWith(".json"))
    .map((f) => JSON.parse(fs.readFileSync(path.join(entriesDir, f), "utf8")) as SoundEntry)
    .filter((e) => !isEntryHidden(e));
}

function assertNoEllipsisTruncation(label: string, text: string) {
  assert.ok(
    !endsWithTruncationEllipsis(text),
    `${label} ends with truncation ellipsis: ${text}`,
  );
}

describe("entry SEO metadata", () => {
  it("keeps every public entry title and description within snippet limits", () => {
    for (const entry of loadPublicCatalog()) {
      const segment = entryPageTitle(entry);
      const docTitle = documentTitleFromSegment(segment, SITE_NAME);
      assert.ok(
        docTitle.length <= TITLE_MAX,
        `${entry.slug} title ${docTitle.length}: ${docTitle}`,
      );
      assertNoEllipsisTruncation(entry.slug, segment);
      assertNoEllipsisTruncation(`${entry.slug} document`, docTitle);
      const desc = entryMetaDescription(entry);
      assert.ok(desc.length <= DESC_MAX, `${entry.slug} desc ${desc.length}`);
      assert.ok(desc.length >= DESC_MIN, `${entry.slug} desc ${desc.length}`);
      assertNoEllipsisTruncation(`${entry.slug} description`, desc);
      assert.ok(desc.includes("Free"), entry.slug);
      assert.ok(desc.includes("CC0"), entry.slug);
    }
  });

  it("shortens known long examples", () => {
    const v8 = loadPublicCatalog().find((e) => e.slug === "v8-engine-rev-8s");
    if (v8) {
      const doc = documentTitleFromSegment(entryPageTitle(v8), SITE_NAME);
      assert.ok(doc.length <= TITLE_MAX);
      assert.ok(doc.includes("V8"));
    }
    const toggle = loadPublicCatalog().find((e) => e.title === "Toggle on");
    if (toggle) {
      const doc = documentTitleFromSegment(entryPageTitle(toggle), SITE_NAME);
      assert.ok(doc.length <= TITLE_MAX);
    }
  });
});

describe("blog SEO metadata", () => {
  it("fits blog post titles and descriptions at render time without ellipsis", () => {
    for (const post of ALL_BLOG_POSTS.filter((p) => !p.draft)) {
      const segment = blogPageTitle(post);
      const doc = documentTitleFromSegment(segment, SITE_NAME);
      assert.ok(doc.length <= TITLE_MAX, `${post.slug} title ${doc.length}`);
      assertNoEllipsisTruncation(post.slug, segment);
      assertNoEllipsisTruncation(`${post.slug} document`, doc);
      const desc = fitMetaDescription(post.description);
      assert.ok(desc.length <= DESC_MAX, post.slug);
      assertNoEllipsisTruncation(`${post.slug} description`, desc);
    }
  });
});

describe("site defaults", () => {
  it("fits the home page default description", () => {
    assert.ok(DEFAULT_SITE_DESCRIPTION.includes("Claude Opus 5.5"));
    assert.ok(DEFAULT_SITE_DESCRIPTION.length <= DESC_MAX);
    const desc = fitMetaDescription(DEFAULT_SITE_DESCRIPTION);
    assert.ok(desc.length <= DESC_MAX);
    assert.ok(desc.length >= DESC_MIN);
    assertNoEllipsisTruncation("home description", desc);
  });
});

describe("category SEO metadata", () => {
  it("fits category hub titles and intros without ellipsis", () => {
    for (const seo of Object.values(CATEGORY_SEO)) {
      const segment = categoryPageTitle(seo);
      const doc = documentTitleFromSegment(segment, SITE_NAME);
      assert.ok(doc.length <= TITLE_MAX, `${seo.h1} → ${doc}`);
      assertNoEllipsisTruncation(seo.h1, segment);
      assertNoEllipsisTruncation(`${seo.h1} document`, doc);
      const desc = categoryPageDescription(seo);
      assert.ok(desc.length <= DESC_MAX, seo.h1);
      assertNoEllipsisTruncation(`${seo.h1} description`, desc);
    }
  });
});
