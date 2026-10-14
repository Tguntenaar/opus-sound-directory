import assert from "node:assert/strict";
import { test } from "node:test";
import { buildHomeBrowseHref } from "./home-browse-url.ts";

test("buildHomeBrowseHref encodes category and search query", () => {
  assert.equal(buildHomeBrowseHref({}), "/");
  assert.equal(buildHomeBrowseHref({ query: "guitar" }), "/?q=guitar");
  assert.equal(buildHomeBrowseHref({ category: "ui", query: "chime" }), "/?category=ui&q=chime");
  assert.equal(buildHomeBrowseHref({ category: "all", query: "  " }), "/");
});
