import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { pickDefaultTake, pickDefaultTakeId } from "./take-selection.ts";
import type { EntryTakeDef } from "./hero8-takes-types.ts";
import { CODEX_MODEL_ID, TARGET_OPUS_MODEL_ID } from "./model-display.ts";

const takes: EntryTakeDef[] = [
  { id: "opus", label: "Opus", modelId: TARGET_OPUS_MODEL_ID, mp3: "/a.mp3" },
  { id: "codex-1", label: "A", modelId: CODEX_MODEL_ID, mp3: "/b.mp3" },
  { id: "codex-2", label: "B", modelId: CODEX_MODEL_ID, mp3: "/c.mp3" },
];

describe("pickDefaultTakeId", () => {
  it("uses opus when no votes", () => {
    assert.equal(pickDefaultTakeId(takes, {}), "opus");
  });

  it("picks highest vote count", () => {
    assert.equal(
      pickDefaultTakeId(takes, { opus: 1, "codex-1": 5, "codex-2": 2 }),
      "codex-1",
    );
  });

  it("keeps opus on tie at the top", () => {
    assert.equal(
      pickDefaultTakeId(takes, { opus: 3, "codex-1": 3, "codex-2": 1 }),
      "opus",
    );
  });
});

describe("pickDefaultTake", () => {
  it("returns honest model id for winning codex take", () => {
    const t = pickDefaultTake(takes, { "codex-2": 4 });
    assert.equal(t.id, "codex-2");
    assert.equal(t.modelId, CODEX_MODEL_ID);
  });
});
