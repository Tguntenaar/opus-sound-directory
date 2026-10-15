import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { describe, it } from "node:test";
import { checkLoudnessMetrics, type CatalogEntryLike } from "./loudness-policy.ts";
import { ffmpegAvailable, measureEbur128 } from "./mp3-true-peak.ts";

const publicRoot = path.join(import.meta.dirname, "../public");
const entriesDir = path.join(import.meta.dirname, "../content/entries");

function loadCatalogEntries(): CatalogEntryLike[] {
  return fs
    .readdirSync(entriesDir)
    .filter((name) => name.endsWith(".json"))
    .map((name) => JSON.parse(fs.readFileSync(path.join(entriesDir, name), "utf8")) as CatalogEntryLike);
}

describe("catalog loudness policy", () => {
  it("every catalog out.mp3 matches integrated/momentary targets and true peak", {
    skip: !ffmpegAvailable(),
  }, () => {
    const failures: string[] = [];
    for (const entry of loadCatalogEntries()) {
      const rel = path.join("assets", entry.id, "out.mp3");
      const file = path.join(publicRoot, rel);
      if (!fs.existsSync(file)) {
        failures.push(`${entry.id}: missing ${rel}`);
        continue;
      }
      const measured = measureEbur128(file);
      const { ok, reasons } = checkLoudnessMetrics(entry, {
        lufs: measured.lufs,
        truePeakDbTp: measured.truePeakDbTp,
        lufsMomentaryMax: measured.lufsMomentaryMax,
      });
      if (!ok) {
        failures.push(`${entry.id}: ${reasons.join("; ")}`);
      }
    }
    assert.equal(
      failures.length,
      0,
      failures.length ? failures.join("\n") : "all catalog MP3s within policy",
    );
  });
});
