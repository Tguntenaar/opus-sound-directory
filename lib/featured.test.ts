import assert from "node:assert/strict";
import { test } from "node:test";
import { featuredVariant, getFeaturedEntry } from "./featured.ts";
import type { SoundEntry } from "./entries-types.ts";

test("Endless riser is the editorial default regardless of catalog order", () => {
  const entries = [{ slug: "chaos-calm-01" }, { slug: "endless-riser-shepard" }] as SoundEntry[];
  assert.equal(getFeaturedEntry(entries), entries[1]);
  assert.equal(getFeaturedEntry([]), null);
  assert.equal(getFeaturedEntry([entries[0]]), entries[0]);
});

test("only configured experiment variants enroll visitors", () => {
  assert.equal(featuredVariant("control"), "control");
  assert.equal(featuredVariant("endless-riser"), "endless-riser");
  for (const value of [undefined, null, false, true, "unknown", ""]) {
    assert.equal(featuredVariant(value), null);
  }
});
