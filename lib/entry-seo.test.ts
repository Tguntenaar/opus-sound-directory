import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { describe, it } from "node:test";
import type { SoundEntry } from "./entries-types.ts";
import { isEntryHidden } from "./entry-visibility.ts";
import { entryMetaDescription, entryPageTitle } from "./entry-seo.ts";
import { CATEGORY_SEO } from "./category-seo.ts";
import { categoryPageDescription, categoryPageTitle } from "./category-seo-meta.ts";
import {
  DESC_MAX,
  DESC_MIN,
  TITLE_MAX,
  documentTitleFromSegment,
} from "./seo-limits.ts";
import { SITE_NAME, DEFAULT_SITE_DESCRIPTION } from "./site-url.ts";
import { ALL_BLOG_POSTS } from "./blog.generated.ts";
import { fitMetaDescription, pickTitleSegment } from "./seo-limits.ts";

const entriesDir = path.join(import.meta.dirname, "../content/entries");

function loadPublicCatalog(): SoundEntry[] {
  return fs
    .readdirSync(entriesDir)
    .filter((f) => f.endsWith(".json"))
    .map((f) => JSON.parse(fs.readFileSync(path.join(entriesDir, f), "utf8")) as SoundEntry)
    .filter((e) => !isEntryHidden(e));
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
      const desc = entryMetaDescription(entry);
      assert.ok(desc.length <= DESC_MAX, `${entry.slug} desc ${desc.length}`);
      assert.ok(desc.length >= DESC_MIN, `${entry.slug} desc ${desc.length}`);
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
  it("fits blog post titles and descriptions at render time", () => {
    for (const post of ALL_BLOG_POSTS.filter((p) => !p.draft)) {
      const doc = documentTitleFromSegment(pickTitleSegment([post.title]), SITE_NAME);
      assert.ok(doc.length <= TITLE_MAX, `${post.slug} title ${doc.length}`);
      const desc = fitMetaDescription(post.description);
      assert.ok(desc.length <= DESC_MAX, post.slug);
    }
  });
});

describe("site defaults", () => {
  it("fits the home page default description", () => {
    const desc = fitMetaDescription(DEFAULT_SITE_DESCRIPTION);
    assert.ok(desc.length <= DESC_MAX);
    assert.ok(desc.length >= DESC_MIN);
  });
});

describe("category SEO metadata", () => {
  it("fits category hub titles and intros", () => {
    for (const seo of Object.values(CATEGORY_SEO)) {
      const doc = documentTitleFromSegment(categoryPageTitle(seo), SITE_NAME);
      assert.ok(doc.length <= TITLE_MAX, `${seo.h1} → ${doc}`);
      const desc = categoryPageDescription(seo.intro);
      assert.ok(desc.length <= DESC_MAX, seo.h1);
    }
  });
});
