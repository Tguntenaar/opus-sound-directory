import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { SPONSOR_PACKAGES } from "./sponsor-packages.ts";

describe("newsletter-social package copy", () => {
  it("does not sell a live newsletter list", () => {
    const pkg = SPONSOR_PACKAGES.find((p) => p.id === "newsletter-social");
    assert.ok(pkg);
    assert.match(pkg.name, /newsletter when list exists/i);
    const copy = [pkg.name, pkg.tagline, ...pkg.bullets].join(" ");
    assert.match(copy, /once (the list exists|we have a list)|when list exists/i);
    assert.doesNotMatch(copy, /newsletter drops/i);
  });
});
