import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { describe, it } from "node:test";
import type { SoundEntry } from "../entries-types.ts";
import { scoreEntry } from "./search-scoring.ts";

const entriesDir = path.join(import.meta.dirname, "../../content/entries");

function loadCatalog(): SoundEntry[] {
  return fs
    .readdirSync(entriesDir)
    .filter((f) => f.endsWith(".json"))
    .map((f) => JSON.parse(fs.readFileSync(path.join(entriesDir, f), "utf8")) as SoundEntry);
}

const CATALOG = loadCatalog();

function topIds(query: string, limit = 5): string[] {
  return CATALOG.map((entry) => ({ entry, score: scoreEntry(entry, query, {}) }))
    .filter((row) => row.score > 0)
    .sort((a, b) => b.score - a.score || a.entry.title.localeCompare(b.entry.title))
    .slice(0, limit)
    .map((row) => row.entry.id);
}

describe("search_sounds ranking", () => {
  it("ranks UI sounds above ad beds for query ui", () => {
    const ids = topIds("ui", 8);
    assert.ok(ids.length >= 2);
    const uiIdx = ids.indexOf("ui-success-chime");
    const adIdx = ids.findIndex((id) => id.startsWith("ad-bed"));
    assert.ok(uiIdx >= 0, "expected ui-success-chime in results");
    if (adIdx >= 0) {
      assert.ok(uiIdx < adIdx, `ui sounds should rank above ad beds: ${ids.join(", ")}`);
    }
    assert.ok(ids[0]?.startsWith("ui-"), `expected a ui-* entry first, got ${ids[0]}`);
    assert.ok(ids[1]?.startsWith("ui-"), `expected ui entries first, got ${ids.join(", ")}`);
  });

  it("ranks whoosh/drop entries for query whoosh", () => {
    const ids = topIds("whoosh", 5);
    assert.ok(ids.some((id) => id.includes("whoosh") || id.includes("drop")));
  });

  it("ranks logo sting for query logo", () => {
    const ids = topIds("logo", 5);
    assert.equal(ids[0], "logo-sting-bright");
  });

  it("ranks riser for query riser", () => {
    const ids = topIds("riser", 5);
    assert.equal(ids[0], "riser-tension-8s");
  });
});
