import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { DEFAULT_NOTIFY_TO, parseNotifyRecipients } from "./sponsor-notify-recipients.ts";
import { sponsorNotifySkipReason } from "./sponsor-notify-skip.ts";
import {
  postSponsorLeadWebhook,
  sponsorLeadWebhookHeaders,
  sponsorLeadWebhookPayload,
} from "./sponsor-notify-webhook.ts";
import type { SponsorLead } from "./sponsor-types.ts";

const sender = {
  send: async () => undefined,
};

const lead: SponsorLead = {
  id: "lead-1",
  createdAt: "2026-10-06T00:00:00.000Z",
  companyName: "Acme",
  contactName: "Ada",
  email: "ada@acme.test",
  website: "https://acme.test",
  packages: ["featured-home"],
  budgetRange: "5-10k",
  message: "Hello",
  ref: "blog-lufs",
};

describe("sponsorNotifySkipReason", () => {
  it("skips when the email binding is missing", () => {
    assert.equal(
      sponsorNotifySkipReason({ SPONSOR_MAIL_FROM: "sponsors@example.com" }),
      "missing SPONSOR_SEND_EMAIL binding",
    );
  });

  it("skips when FROM is missing", () => {
    assert.equal(
      sponsorNotifySkipReason({ SPONSOR_SEND_EMAIL: sender }),
      "missing SPONSOR_MAIL_FROM",
    );
    assert.equal(
      sponsorNotifySkipReason({ SPONSOR_SEND_EMAIL: sender, SPONSOR_MAIL_FROM: "  " }),
      "missing SPONSOR_MAIL_FROM",
    );
  });

  it("allows send when both binding and FROM are set", () => {
    assert.equal(
      sponsorNotifySkipReason({
        SPONSOR_SEND_EMAIL: sender,
        SPONSOR_MAIL_FROM: "sponsors@example.com",
      }),
      null,
    );
  });
});

describe("parseNotifyRecipients", () => {
  it("defaults to Olivier then Thomas when unset or empty", () => {
    assert.deepEqual(DEFAULT_NOTIFY_TO, [
      "olivierguntenaar@gmail.com",
      "thomas@guntenaar.org",
    ]);
    assert.deepEqual(parseNotifyRecipients(undefined), [...DEFAULT_NOTIFY_TO]);
    assert.deepEqual(parseNotifyRecipients(null), [...DEFAULT_NOTIFY_TO]);
    assert.deepEqual(parseNotifyRecipients(""), [...DEFAULT_NOTIFY_TO]);
    assert.deepEqual(parseNotifyRecipients("  "), [...DEFAULT_NOTIFY_TO]);
    assert.deepEqual(parseNotifyRecipients(" , ; "), [...DEFAULT_NOTIFY_TO]);
  });

  it("parses comma and semicolon lists, trim/lowercase/dedupe/drop empties", () => {
    assert.deepEqual(parseNotifyRecipients("a@x,b@y"), ["a@x", "b@y"]);
    assert.deepEqual(parseNotifyRecipients("A@X; B@Y"), ["a@x", "b@y"]);
    assert.deepEqual(parseNotifyRecipients(" a@x ,, ; b@y ,A@X "), ["a@x", "b@y"]);
  });
});

describe("sponsor lead webhook", () => {
  it("posts the lead fields and optional Bearer key", () => {
    assert.deepEqual(sponsorLeadWebhookPayload(lead), {
      id: "lead-1",
      companyName: "Acme",
      website: "https://acme.test",
      contactName: "Ada",
      email: "ada@acme.test",
      packages: ["featured-home"],
      budgetRange: "5-10k",
      message: "Hello",
      ref: "blog-lufs",
      createdAt: "2026-10-06T00:00:00.000Z",
    });
    assert.deepEqual(sponsorLeadWebhookHeaders(undefined), {
      "content-type": "application/json",
    });
    assert.deepEqual(sponsorLeadWebhookHeaders("  secret  "), {
      "content-type": "application/json",
      Authorization: "Bearer secret",
    });
  });

  it("skips fetch when webhook URL is unset", async () => {
    let called = 0;
    const fetchFn = (async () => {
      called += 1;
      return new Response(null, { status: 204 });
    }) as typeof fetch;
    await postSponsorLeadWebhook(lead, {}, fetchFn);
    await postSponsorLeadWebhook(lead, { SPONSOR_NOTIFY_WEBHOOK_URL: "  " }, fetchFn);
    assert.equal(called, 0);
  });

  it("POSTs JSON and never throws on webhook failure", async () => {
    const calls: { url: string; init: RequestInit }[] = [];
    const fetchFn = (async (url: string | URL | Request, init?: RequestInit) => {
      calls.push({ url: String(url), init: init ?? {} });
      return new Response("nope", { status: 503 });
    }) as typeof fetch;

    await postSponsorLeadWebhook(
      lead,
      {
        SPONSOR_NOTIFY_WEBHOOK_URL: "https://hooks.example/lead",
        SPONSOR_NOTIFY_WEBHOOK_KEY: "k",
      },
      fetchFn,
    );
    assert.equal(calls.length, 1);
    assert.equal(calls[0].url, "https://hooks.example/lead");
    assert.equal(calls[0].init.method, "POST");
    assert.equal(
      (calls[0].init.headers as Record<string, string>).Authorization,
      "Bearer k",
    );
    assert.equal(calls[0].init.body, JSON.stringify(sponsorLeadWebhookPayload(lead)));

    const boom = (async () => {
      throw new Error("network");
    }) as typeof fetch;
    await postSponsorLeadWebhook(
      lead,
      { SPONSOR_NOTIFY_WEBHOOK_URL: "https://hooks.example/lead" },
      boom,
    );
  });
});
