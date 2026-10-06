import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  NEW_BADGE_THRESHOLD,
  isLowPublicStatCount,
  isPublicStatCountVisible,
  shouldShowNewStatBadge,
} from "./stats-display.ts";

describe("stats display threshold", () => {
  it("uses threshold 10", () => {
    assert.equal(NEW_BADGE_THRESHOLD, 10);
  });

  it("treats counts below threshold as low", () => {
    assert.equal(isLowPublicStatCount(0), true);
    assert.equal(isLowPublicStatCount(9), true);
    assert.equal(isLowPublicStatCount(10), false);
    assert.equal(isPublicStatCountVisible(10), true);
    assert.equal(isPublicStatCountVisible(9), false);
  });

  it("shows one new badge when any counter is low", () => {
    assert.equal(shouldShowNewStatBadge([15, 3]), true);
    assert.equal(shouldShowNewStatBadge([12, 11]), false);
    assert.equal(shouldShowNewStatBadge([0, 0]), true);
  });
});
