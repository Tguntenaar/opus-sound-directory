import assert from "node:assert/strict";
import { test } from "node:test";
import {
  canApplyFeaturedVariant,
  featuredVariant,
  getFeaturedEntry,
  resolveFeaturedSound,
} from "./featured.ts";
import type { SoundEntry } from "./entries-types.ts";

test("Endless riser is the editorial default regardless of catalog order", () => {
  const entries = [{ slug: "chaos-calm-01" }, { slug: "endless-riser-shepard" }] as SoundEntry[];
  assert.equal(getFeaturedEntry(entries), entries[1]);
  assert.equal(getFeaturedEntry([]), null);
  assert.equal(getFeaturedEntry([entries[0]]), entries[0]);
});

test("resolveFeaturedSound maps variants to entry or control", () => {
  const entry = { id: "e1", slug: "endless-riser-shepard" } as SoundEntry;
  const control = { id: "c1", slug: "chaos-calm-01" } as SoundEntry;
  assert.equal(resolveFeaturedSound(null, entry, control), entry);
  assert.equal(resolveFeaturedSound("endless-riser", entry, control), entry);
  assert.equal(resolveFeaturedSound("control", entry, control), control);
  assert.equal(resolveFeaturedSound("control", entry), entry);
});

test("canApplyFeaturedVariant blocks swaps during featured playback", () => {
  const entry = { id: "e1", slug: "endless-riser-shepard" } as SoundEntry;
  const control = { id: "c1", slug: "chaos-calm-01" } as SoundEntry;
  assert.equal(canApplyFeaturedVariant("control", entry, entry, control, false), true);
  assert.equal(canApplyFeaturedVariant("control", entry, entry, control, true), false);
  assert.equal(canApplyFeaturedVariant(null, control, entry, control, true), false);
  assert.equal(canApplyFeaturedVariant("endless-riser", entry, entry, control, true), true);
});

test("only configured experiment variants enroll visitors", () => {
  assert.equal(featuredVariant("control"), "control");
  assert.equal(featuredVariant("endless-riser"), "endless-riser");
  for (const value of [undefined, null, false, true, "unknown", ""]) {
    assert.equal(featuredVariant(value), null);
  }
});
