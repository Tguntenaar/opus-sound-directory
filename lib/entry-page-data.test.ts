import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { describe, it } from "node:test";
import { z } from "zod";
import type { SoundEntry } from "./entries-types.ts";
import { isEntryHidden } from "./entry-visibility.ts";
import { CATEGORIES } from "./categories.ts";

const entriesDir = path.join(import.meta.dirname, "../content/entries");
const publicRoot = path.join(import.meta.dirname, "../public");

const cueSchema = z.object({
  frame: z.number(),
  label: z.string(),
});

/** JSON shape the /e/[slug] page and SEO helpers assume for catalog entries. */
export const catalogEntrySchema = z.object({
  id: z.string().min(1),
  slug: z.string().min(1),
  title: z.string().min(1),
  category: z.string().min(1),
  tags: z.array(z.string()),
  mood: z.array(z.string()),
  tempo: z.enum(["slow", "medium", "fast"]).optional(),
  prompt: z.string().min(1),
  modelId: z.string().min(1),
  targetModelId: z.string().optional(),
  generatedAt: z.string().min(1),
  seed: z.number(),
  timing: z.object({
    bpm: z.number().optional(),
    fps: z.number(),
    durationSec: z.number(),
    samples: z.number(),
    sampleRate: z.number(),
  }),
  cues: z.array(cueSchema).optional(),
  master: z.object({
    targetLufs: z.number(),
    truePeakDbTp: z.number(),
  }),
  metrics: z.object({
    lufs: z.number().nullable(),
    truePeak: z.number().nullable(),
    lufsMomentaryMax: z.number().nullable().optional(),
    lufsShortTermMax: z.number().nullable().optional(),
    durationSec: z.number().nullable(),
    passedChecks: z.boolean(),
    measuredFrom: z.string().optional(),
    shippedSampleRate: z.number().optional(),
    downsampled: z.boolean().optional(),
    note: z.string().optional(),
  }),
  assets: z.object({
    wav: z.string().min(1),
    mp3: z.string().min(1),
    spectrogram: z.string(),
    code: z.string().min(1),
  }),
  notes: z.string(),
  hidden: z.boolean().optional(),
});

function loadAllEntries(): SoundEntry[] {
  return fs
    .readdirSync(entriesDir)
    .filter((f) => f.endsWith(".json"))
    .map((f) => JSON.parse(fs.readFileSync(path.join(entriesDir, f), "utf8")) as SoundEntry);
}

function loadPublicCatalog(): SoundEntry[] {
  return loadAllEntries().filter((e) => !isEntryHidden(e));
}

/** Mirrors fields dereferenced on app/e/[slug]/page.tsx (static catalog path). */
function exerciseEntryPageDataPath(entry: SoundEntry) {
  const catLabel = CATEGORIES[entry.category]?.label ?? entry.category;
  assert.ok(catLabel.length > 0);

  assert.ok(entry.title.length > 0);
  assert.ok(entry.generatedAt.length > 0);
  assert.ok(entry.prompt.length > 0);
  assert.ok(entry.slug.length > 0);

  assert.equal(typeof entry.timing.fps, "number");
  assert.equal(typeof entry.timing.durationSec, "number");
  assert.equal(typeof entry.seed, "number");
  assert.equal(typeof entry.metrics.lufs, "number");
  assert.equal(typeof entry.metrics.truePeak, "number");

  const cues = entry.cues ?? [];
  for (const c of cues) {
    assert.equal(typeof c.frame, "number");
    assert.equal(typeof c.label, "string");
    const line = `Frame ${c.frame}: ${c.label}`;
    assert.ok(line.length > 0);
  }

  if (entry.notes) {
    assert.ok(entry.notes.length >= 0);
  }

  assert.ok(entry.assets.code.startsWith("/assets/"));
  assert.ok(entry.assets.mp3.startsWith("/assets/") || entry.assets.mp3.startsWith("http"));
  assert.ok(entry.assets.wav.startsWith("/assets/") || entry.assets.wav.startsWith("http"));
  if (entry.assets.spectrogram) {
    assert.ok(
      entry.assets.spectrogram.startsWith("/assets/") ||
        entry.assets.spectrogram.startsWith("http"),
    );
  }

  for (const m of entry.mood ?? []) {
    assert.ok(typeof m === "string" && m.length > 0);
  }
}

const PUBLIC = loadPublicCatalog();

describe("catalog entry JSON", () => {
  it("validates every on-disk entry against the catalog schema", () => {
    for (const entry of loadAllEntries()) {
      const parsed = catalogEntrySchema.safeParse(entry);
      assert.ok(
        parsed.success,
        `${entry.id}: ${parsed.success ? "" : JSON.stringify(parsed.error.flatten())}`,
      );
    }
  });
});

describe("entry page data path", () => {
  it("exercises /e/[slug] field access for every public catalog entry", () => {
    for (const entry of PUBLIC) {
      exerciseEntryPageDataPath(entry);
    }
  });

  it("static asset paths exist for every public entry", () => {
    for (const entry of PUBLIC) {
      for (const rel of [entry.assets.wav, entry.assets.mp3, entry.assets.code]) {
        if (rel.startsWith("http")) continue;
        const disk = path.join(publicRoot, rel.replace(/^\//, ""));
        assert.ok(fs.existsSync(disk), `${entry.id}: missing ${rel}`);
      }
      if (entry.assets.spectrogram && !entry.assets.spectrogram.startsWith("http")) {
        const disk = path.join(publicRoot, entry.assets.spectrogram.replace(/^\//, ""));
        assert.ok(fs.existsSync(disk), `${entry.id}: missing spectrogram`);
      }
    }
  });
});
