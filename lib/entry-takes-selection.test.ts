import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { describe, it } from "node:test";
import type { SoundEntry } from "./entries-types.ts";
import { isEntryHidden } from "./entry-visibility.ts";
import { passesTakeQuality } from "./hero8-take-quality.ts";
import { HERO8_CODEX_TAKE_ROWS } from "./hero8-takes.generated.ts";
import type { EntryTakeDef, EntryTakeId } from "./hero8-takes-types.ts";
import { CODEX_MODEL_ID, TARGET_OPUS_MODEL_ID } from "./model-display.ts";
import { pickDefaultTake, pickDefaultTakeId } from "./take-selection.ts";

const HERO8_VOTING_ENTRY_IDS: readonly string[] = [
  "heavy-boom-meme",
  "whoosh-pass-by",
  "ui-cozy-sprite",
  "endless-riser-shepard",
  "dialup-modem-56k",
  "wah-wah-fail",
  "arcade-game-over",
  "trailer-braam-hit",
  "game-coin-pickup",
];

const CODEX_LABELS: Record<number, string> = { 1: "A", 2: "B", 3: "C" };

const entriesDir = path.join(import.meta.dirname, "../content/entries");

function loadPublicCatalog(): SoundEntry[] {
  return fs
    .readdirSync(entriesDir)
    .filter((f) => f.endsWith(".json"))
    .map((f) => JSON.parse(fs.readFileSync(path.join(entriesDir, f), "utf8")) as SoundEntry)
    .filter((e) => !isEntryHidden(e));
}

/** Same take list as EntryTakesPlayer (relative-import copy for node:test). */
function entryTakesFor(entry: Pick<SoundEntry, "id" | "modelId" | "assets">): EntryTakeDef[] {
  if (!HERO8_VOTING_ENTRY_IDS.includes(entry.id)) return [];
  const codex = HERO8_CODEX_TAKE_ROWS.filter((r) => r.entryId === entry.id)
    .filter((r) => passesTakeQuality(r))
    .map((r) => ({
      id: r.takeId as EntryTakeId,
      label: CODEX_LABELS[r.codexTake] ?? String(r.codexTake),
      modelId: CODEX_MODEL_ID,
      mp3: r.mp3,
      wav: r.wav,
      lufs: r.lufs,
      truePeakDbTp: r.truePeakDbTp,
    }));
  if (codex.length === 0) return [];

  const opus: EntryTakeDef = {
    id: "opus",
    label: "Opus",
    modelId: entry.modelId || TARGET_OPUS_MODEL_ID,
    mp3: entry.assets.mp3 ?? "",
    wav: entry.assets.wav,
    lufs: undefined,
    truePeakDbTp: undefined,
  };
  if (!opus.mp3) return codex;
  return [opus, ...codex];
}

function resolveActiveTake(entry: SoundEntry, votes: Record<string, number> = {}) {
  const takes = entryTakesFor(entry);
  const selectedId = pickDefaultTakeId(takes, votes);
  return takes.find((t) => t.id === selectedId) ?? pickDefaultTake(takes, votes);
}

describe("entry takes player selection", () => {
  it("resolves every catalog entry without undefined activeTake model access", () => {
    const entries = loadPublicCatalog();
    assert.ok(entries.length >= 46, "expected full public catalog");

    for (const entry of entries) {
      const takes = entryTakesFor(entry);
      const activeTake = resolveActiveTake(entry);

      if (takes.length <= 1 || !activeTake) {
        assert.ok(entry.modelId, `${entry.id}: fallback uses entry.modelId`);
        continue;
      }

      const modelId = activeTake.modelId ?? entry.modelId;
      assert.ok(modelId, `${entry.id}: playback modelId must be defined`);
    }
  });
});
