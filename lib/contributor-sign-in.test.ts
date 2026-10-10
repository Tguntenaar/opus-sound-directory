import { test } from "node:test";
import assert from "node:assert/strict";
import { shouldShowBookmarkSignInUnavailable, shouldShowContributorSignIn } from "./contributor-sign-in.ts";

test("contributor sign-in card appears on first paint when providers are known", () => {
  assert.equal(shouldShowContributorSignIn(null, true, ["github", "google"], false), true);
  assert.equal(shouldShowContributorSignIn(null, true, [], false), false);
  assert.equal(shouldShowContributorSignIn(null, true, [], true), true);
  assert.equal(shouldShowContributorSignIn({ id: "u" }, true, ["github"], false), false);
  assert.equal(shouldShowContributorSignIn(null, false, [], true), true);
});

test("bookmark dialog hides unavailable until provider list is known", () => {
  assert.equal(shouldShowBookmarkSignInUnavailable(false, [], ""), false);
  assert.equal(shouldShowBookmarkSignInUnavailable(true, ["github"], ""), false);
  assert.equal(shouldShowBookmarkSignInUnavailable(true, [], ""), true);
  assert.equal(shouldShowBookmarkSignInUnavailable(true, [], "oops"), false);
});
