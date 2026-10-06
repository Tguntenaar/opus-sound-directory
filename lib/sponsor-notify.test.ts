import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { sponsorNotifySkipReason } from "./sponsor-notify-skip.ts";

const sender = {
  send: async () => undefined,
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
