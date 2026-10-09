import test from "node:test";
import assert from "node:assert/strict";
import { parseReviewJson, reviewAllowsPublication } from "./submit-review-policy.ts";
import { staticScreenSubmission } from "./submit-screen.ts";

const safe = { verdict: "safe", quality: 4, categoryFit: true, reasons: [], rightsConcerns: [] };
test("incomplete and malformed AI reviews never grant approval", () => {
  for (const value of [{ ...safe, categoryFit: "false" }, { ...safe, quality: "4" }, { ...safe, rightsConcerns: undefined }, { ...safe, reasons: [7] }, { ...safe, quality: 6 }]) {
    assert.equal(parseReviewJson(JSON.stringify(value), "test"), null);
  }
  const review = parseReviewJson(JSON.stringify(safe), "test")!;
  assert.equal(reviewAllowsPublication(review, {}), true);
  assert.equal(reviewAllowsPublication({ ...review, complete: false }, {}), false);
  assert.equal(reviewAllowsPublication({ ...review, rightsConcerns: ["Sample licensing unclear"] }, {}), false);
  assert.equal(reviewAllowsPublication(review, { suspiciousClaims: ["attribution"] }), false);
  assert.equal(reviewAllowsPublication(review, { spam: true }), false);
});
test("normal WAV output is allowed, while executable process and network flags remain", () => {
  const entry = { title: "Chime", prompt: "Create a small synthesized sound using sine waves.", email: "a@example.test", category: "ui", mood: ["calm"], code: "import wave\nwith wave.open('out.wav', 'wb') as out:\n    out.setnchannels(1)" };
  assert.equal(staticScreenSubmission(entry).ok, true);
  assert.equal(staticScreenSubmission({ ...entry, code: "import subprocess\nsubprocess.run(['whoami'])" }).ok, false);
});
