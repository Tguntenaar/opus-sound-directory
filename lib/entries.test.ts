import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { describe, it } from "node:test";
import type { SoundEntry } from "./entries-types.ts";
import { isEntryHidden } from "./entry-visibility.ts";

const entriesDir = path.join(import.meta.dirname, "../content/entries");

function loadPublicCatalog(): SoundEntry[] {
  return fs
    .readdirSync(entriesDir)
    .filter((f) => f.endsWith(".json"))
    .map((f) => JSON.parse(fs.readFileSync(path.join(entriesDir, f), "utf8")) as SoundEntry)
    .filter((e) => !isEntryHidden(e));
}

describe("hidden catalog entries", () => {
  it("omits hidden entries from the public catalog", () => {
    const ids = loadPublicCatalog().map((e) => e.id);
    assert.ok(!ids.includes("ui-camera-shutter"));
    assert.equal(loadPublicCatalog().length, 39);
  });

  it("marks ui-camera-shutter hidden in content", () => {
    const shutter = JSON.parse(
      fs.readFileSync(path.join(entriesDir, "ui-camera-shutter.json"), "utf8"),
    ) as SoundEntry;
    assert.ok(isEntryHidden(shutter));
  });
});
