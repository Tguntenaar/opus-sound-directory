import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { shouldServeMcpInfoPage } from "./should-serve-info-page.ts";

function get(url: string, headers: Record<string, string> = {}) {
  return new Request(url, { method: "GET", headers });
}

describe("shouldServeMcpInfoPage", () => {
  it("serves info for vinext RSC prefetch", () => {
    assert.equal(
      shouldServeMcpInfoPage(get("https://opussounds.directory/mcp?_rsc=abc")),
      true,
    );
  });

  it("delegates to MCP handler when session header is present", () => {
    assert.equal(
      shouldServeMcpInfoPage(
        get("https://opussounds.directory/mcp", { "mcp-session-id": "s1" }),
      ),
      false,
    );
  });

  it("serves info for normal browser navigation", () => {
    assert.equal(
      shouldServeMcpInfoPage(
        get("https://opussounds.directory/mcp", {
          Accept: "text/html,application/xhtml+xml",
        }),
      ),
      true,
    );
  });
});
