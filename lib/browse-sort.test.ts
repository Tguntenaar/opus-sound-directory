import assert from "node:assert/strict";
import { test } from "node:test";
import { popularityScore, sortEntries } from "./browse-sort.ts";
import type { SoundEntry } from "./entries-types.ts";

const entry = (id: string, generatedAt: string) => ({ id, generatedAt }) as SoundEntry;
test("popularity weights reuse intent and accepts legacy counters", () => {
  assert.equal(popularityScore("a", { a: { play: 2, copy: 1, download: 1 } }), 10);
  assert.equal(popularityScore("missing", {}), 0);
  assert.equal(popularityScore("a", { a: { copy: 1, download: 1 } } as never), 8);
});
test("popular ranks usage; newest remains chronological; input is unchanged", () => {
  const entries = [entry("old", "2025-01-01"), entry("new", "2026-01-01")];
  const stats = { old: { play: 10, copy: 0, download: 0 } };
  assert.deepEqual(sortEntries(entries, "popular", stats).map(e => e.id), ["old", "new"]);
  assert.deepEqual(sortEntries(entries, "new", stats).map(e => e.id), ["new", "old"]);
  assert.deepEqual(sortEntries(entries, "popular", {}).map(e => e.id), ["new", "old"]);
  assert.equal(entries[0].id, "old");
});
test("popular with empty stats uses editorial seed before newer long beds", () => {
  const entries = [
    entry("bass-wobble-drop-150", "2026-09-01"),
    entry("heavy-boom-meme", "2025-01-01"),
    entry("calendar-chaos-to-order-33s", "2026-08-01"),
    entry("whoosh-pass-by", "2025-02-01"),
  ];
  const order = sortEntries(entries, "popular", {}).map(e => e.id);
  assert.deepEqual(order.slice(0, 2), ["heavy-boom-meme", "whoosh-pass-by"]);
  assert.ok(order.indexOf("heavy-boom-meme") < order.indexOf("bass-wobble-drop-150"));
  assert.ok(order.indexOf("whoosh-pass-by") < order.indexOf("calendar-chaos-to-order-33s"));
});
test("popular still prefers higher real popularity over editorial seed", () => {
  const entries = [
    entry("heavy-boom-meme", "2025-01-01"),
    entry("bass-wobble-drop-150", "2026-09-01"),
  ];
  const stats = { "bass-wobble-drop-150": { play: 1, copy: 0, download: 0 } };
  assert.deepEqual(sortEntries(entries, "popular", stats).map(e => e.id), [
    "bass-wobble-drop-150",
    "heavy-boom-meme",
  ]);
});
