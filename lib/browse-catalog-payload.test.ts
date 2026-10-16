import assert from "node:assert/strict";
import { describe, it } from "node:test";
import type { SoundEntry } from "./entries-types.ts";
import { slimEntriesForBrowse } from "./browse-catalog-payload.ts";

const base: SoundEntry = {
  id: "test",
  slug: "test",
  title: "Test",
  category: "ui-sounds",
  tags: ["ui"],
  mood: ["bright"],
  prompt: "x".repeat(400),
  modelId: "claude-opus-5-5",
  generatedAt: "2026-10-01",
  seed: 1,
  timing: { fps: 30, durationSec: 1, samples: 48000, sampleRate: 48000 },
  master: { targetLufs: -14, truePeakDbTp: -1 },
  metrics: {
    lufs: -14,
    truePeak: -2,
    durationSec: 1,
    passedChecks: true,
  },
  assets: {
    wav: "/a.wav",
    mp3: "/a.mp3",
    spectrogram: "/a.png",
    code: "/a.py",
  },
  notes: "long notes",
  cues: [{ frame: 0, label: "hit" }],
};

describe("slimEntriesForBrowse", () => {
  it("truncates prompt and drops browse-only bloat", () => {
    const [out] = slimEntriesForBrowse([base]);
    assert.equal(out.prompt.length, 200);
    assert.equal(out.notes, "");
    assert.equal(out.cues, undefined);
    assert.equal(out.title, base.title);
  });
});
