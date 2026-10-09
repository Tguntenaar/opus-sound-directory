import { test } from "node:test";
import assert from "node:assert/strict";
import { parseSignInAttempt } from "./auth-analytics.ts";

test("OAuth attribution accepts both providers and strips unexpected account data", () => {
  for (const provider of ["github", "google"]) {
    assert.deepEqual(parseSignInAttempt(JSON.stringify({ provider, source: "submit", startedAt: 1000, email: "private@example.test" }), 2000), { provider, source: "submit", startedAt: 1000 });
  }
});

test("OAuth attribution rejects malformed, expired, future and unknown attempts", () => {
  for (const value of [null, "bad", "null", "{}", JSON.stringify({ provider: "other", source: "account", startedAt: 1000 }), JSON.stringify({ provider: "github", source: "other", startedAt: 1000 }), JSON.stringify({ provider: "github", source: "account", startedAt: 3000 }), JSON.stringify({ provider: "github", source: "account", startedAt: -3600000 })]) {
    assert.equal(parseSignInAttempt(value, 2000), null);
  }
});
