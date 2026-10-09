import assert from "node:assert/strict";
import { test } from "node:test";
import fs from "node:fs";
import { toSearchRecords, searchCatalog } from "./search-records.ts";
import type { SoundEntry } from "./entries-types.ts";

const entries: SoundEntry[] = fs.readdirSync(new URL("../content/entries/", import.meta.url))
  .filter((file) => file.endsWith(".json"))
  .map((file) => JSON.parse(fs.readFileSync(new URL(`../content/entries/${file}`, import.meta.url), "utf8")));

test("search feed excludes hidden sounds and private or large source fields", () => {
  const records = toSearchRecords(entries);
  assert.equal(records.length, entries.filter((entry) => !entry.hidden).length);
  assert.ok(!records.some((record) => record.slug === "ui-camera-shutter"));
  assert.ok(records.every((record) => !("assets" in record) && !("submissionId" in record)));
  assert.equal(new Set(records.map((record) => record.objectID)).size, records.length);
  assert.ok(records.every((record) => Buffer.byteLength(JSON.stringify(record)) < 10_000));
});

test("catalog fallback matches multiple terms without case sensitivity and caps results", () => {
  const records = toSearchRecords(entries);
  const result = searchCatalog(records, "SUCCESS CHIME");
  assert.ok(result.hits.some((record) => record.slug === "ui-success-chime"));
  assert.equal(searchCatalog(records, "zzznomatchzzz").nbHits, 0);
  const all = searchCatalog(records, "");
  assert.equal(all.nbHits, records.length);
  assert.equal(all.hits.length, 12);
});

test("search records carry audio previews only when rendered audio is available", () => {
  const entry = entries.find(entry => !entry.hidden)!;
  assert.equal(toSearchRecords([entry])[0].previewUrl, entry.assets.mp3);
  assert.equal(toSearchRecords([{ ...entry, isCommunity: true, hasRenderedAudio: false }])[0].previewUrl, null);
  assert.equal(toSearchRecords([{ ...entry, assets: { ...entry.assets, mp3: "" } }])[0].previewUrl, entry.assets.wav);
});
