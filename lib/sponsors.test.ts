import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { describe, it } from "node:test";
import {
  isActiveSponsor,
  resolveBlogSponsor,
  resolveCategorySponsor,
  resolveHomeSponsor,
  withSponsorUtm,
  type ActiveSponsor,
  type SponsorsFile,
} from "./sponsor-resolve.ts";

const acme: ActiveSponsor = {
  name: "Acme Audio",
  logo: "/sponsors/acme.svg",
  line: "Sound kits for short-form video.",
  url: "https://acme.example",
  utm: "utm_source=opus-sounds&utm_medium=sponsor&utm_campaign=home",
};

const empty: SponsorsFile = {
  blog: { active: null, bySlug: {} },
  home: null,
  categories: {},
};

describe("shipped sponsors.json", () => {
  it("keeps home and categories empty until a sale is filled in", () => {
    const raw = JSON.parse(
      fs.readFileSync(path.join(import.meta.dirname, "../content/sponsors.json"), "utf8"),
    ) as { home: unknown; categories: unknown; blog: unknown };
    assert.equal(raw.home, null);
    assert.deepEqual(raw.categories, {});
    assert.equal(typeof raw.blog, "object");
  });
});

describe("isActiveSponsor", () => {
  it("accepts a complete sponsor", () => {
    assert.equal(isActiveSponsor(acme), true);
  });

  it("rejects null, missing name, or missing url", () => {
    assert.equal(isActiveSponsor(null), false);
    assert.equal(isActiveSponsor({ ...acme, name: "" }), false);
    assert.equal(isActiveSponsor({ ...acme, url: "  " }), false);
    assert.equal(isActiveSponsor({ name: "x" }), false);
  });
});

describe("resolveHomeSponsor", () => {
  it("returns null when home is unset", () => {
    assert.equal(resolveHomeSponsor(empty), null);
  });

  it("returns the home sponsor when set", () => {
    assert.deepEqual(resolveHomeSponsor({ ...empty, home: acme }), acme);
  });
});

describe("resolveCategorySponsor", () => {
  it("returns a category sponsor only for that shelf", () => {
    const file: SponsorsFile = { ...empty, categories: { "ui-sounds": acme } };
    assert.deepEqual(resolveCategorySponsor(file, "ui-sounds"), acme);
    assert.equal(resolveCategorySponsor(file, "drops"), null);
    assert.equal(resolveCategorySponsor(file, ""), null);
  });
});

describe("resolveBlogSponsor", () => {
  it("prefers bySlug over active", () => {
    const perPost: ActiveSponsor = { ...acme, name: "Per-post" };
    const file: SponsorsFile = {
      blog: { active: acme, bySlug: { "podcast-intro-music": perPost } },
    };
    assert.equal(resolveBlogSponsor(file, "podcast-intro-music")?.name, "Per-post");
    assert.equal(resolveBlogSponsor(file, "other-slug")?.name, "Acme Audio");
  });
});

describe("withSponsorUtm", () => {
  it("appends utm and leaves the url alone when utm is empty", () => {
    assert.equal(withSponsorUtm("https://acme.example", undefined), "https://acme.example");
    assert.equal(
      withSponsorUtm("https://acme.example", "utm_source=opus-sounds"),
      "https://acme.example?utm_source=opus-sounds",
    );
    assert.equal(
      withSponsorUtm("https://acme.example?ref=1", "utm_medium=sponsor"),
      "https://acme.example?ref=1&utm_medium=sponsor",
    );
  });
});
