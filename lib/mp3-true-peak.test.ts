import assert from "node:assert/strict";
import path from "node:path";
import { describe, it } from "node:test";
import {
  ffmpegAvailable,
  listPublicMp3Files,
  measureEbur128,
  MP3_TRUE_PEAK_CEILING_DBTP,
  mp3PassesTruePeakCeiling,
} from "./mp3-true-peak.ts";

const publicRoot = path.join(import.meta.dirname, "../public");

describe("public MP3 true peak (ebur128)", () => {
  it("every public/assets MP3 decodes at or below -1.0 dBTP", { skip: !ffmpegAvailable() }, () => {
    const files = listPublicMp3Files(publicRoot);
    assert.ok(files.length > 0, "expected catalog MP3 assets under public/assets");
    const failures: string[] = [];
    for (const file of files) {
      const { truePeakDbTp, lufs } = measureEbur128(file);
      if (!mp3PassesTruePeakCeiling(truePeakDbTp)) {
        const rel = path.relative(publicRoot, file);
        failures.push(
          `${rel}: peak=${truePeakDbTp} LUFS=${lufs} (ceiling ${MP3_TRUE_PEAK_CEILING_DBTP} dBTP)`,
        );
      }
    }
    assert.equal(
      failures.length,
      0,
      failures.length ? failures.join("\n") : "all MP3s within true-peak ceiling",
    );
  });
});
