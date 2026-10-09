import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { passesTakeQuality } from "./hero8-take-quality.ts";
import { HERO8_CODEX_TAKE_ROWS } from "./hero8-takes.generated.ts";

describe("passesTakeQuality", () => {
  it("accepts hero8 measurement rows", () => {
    for (const row of HERO8_CODEX_TAKE_ROWS) {
      assert.equal(
        passesTakeQuality({ lufs: row.lufs, truePeakDbTp: row.truePeakDbTp }),
        true,
        row.entryId + " " + row.takeId,
      );
    }
  });

  it("rejects clipped peaks", () => {
    assert.equal(passesTakeQuality({ lufs: -14, truePeakDbTp: -0.5 }), false);
  });
});
