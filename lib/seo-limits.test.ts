import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  DESC_MAX,
  TITLE_MAX,
  documentTitleFromSegment,
  fitMetaDescription,
  maxTitleSegmentLength,
  pickTitleSegment,
  truncateAtWordBoundary,
} from "./seo-limits.ts";
import { SITE_NAME } from "./site-url.ts";

describe("seo-limits", () => {
  it("truncates on word boundaries with ellipsis", () => {
    const out = truncateAtWordBoundary("one two three four five", 12);
    assert.ok(out.endsWith("…"));
    assert.ok(out.length <= 12);
    assert.ok(!out.includes("four"));
  });

  it("fits document titles under TITLE_MAX", () => {
    const long =
      "V8 engine start and rev — Free Foley Sound Effect (WAV, MP3, CC0)";
    const segment = pickTitleSegment([
      long,
      "V8 engine start and rev — Free Foley SFX (CC0)",
      "V8 engine start and rev — Free Foley SFX",
    ]);
    const doc = documentTitleFromSegment(segment, SITE_NAME);
    assert.ok(doc.length <= TITLE_MAX, doc);
    assert.ok(segment.includes("Free"));
  });

  it("caps meta descriptions at DESC_MAX", () => {
    const long = "a".repeat(200);
    assert.equal(fitMetaDescription(long).length, DESC_MAX);
  });

  it("max title segment accounts for site suffix", () => {
    const segment = "x".repeat(maxTitleSegmentLength(SITE_NAME));
    assert.equal(documentTitleFromSegment(segment, SITE_NAME).length, TITLE_MAX);
  });
});
