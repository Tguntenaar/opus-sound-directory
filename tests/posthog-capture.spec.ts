import { test, expect } from "./fixtures";
import { gunzipSync, inflateSync } from "zlib";

function decodePostBody(buffer: Buffer | null): string {
  if (!buffer || buffer.length === 0) return "";
  const asText = buffer.toString("utf8");
  if (asText.startsWith("{") || asText.startsWith("[") || asText.includes('"event"')) {
    return asText;
  }
  if (asText.startsWith("data=")) {
    try {
      return Buffer.from(asText.slice(5), "base64").toString("utf8");
    } catch {
      return asText;
    }
  }
  try {
    return gunzipSync(buffer).toString("utf8");
  } catch {
    try {
      return inflateSync(buffer).toString("utf8");
    } catch {
      return asText;
    }
  }
}

function eventsFromPostBody(body: string): string[] {
  const names: string[] = [];
  const pushFromUnknown = (value: unknown) => {
    if (!value || typeof value !== "object") return;
    const event = (value as { event?: string }).event;
    if (event) names.push(event);
  };
  try {
    const json = JSON.parse(body) as {
      event?: string;
      batch?: unknown[];
      data?: unknown;
    };
    if (json.event) names.push(json.event);
    if (Array.isArray(json.batch)) {
      for (const item of json.batch) pushFromUnknown(item);
    }
    pushFromUnknown(json.data);
  } catch {
    for (const match of body.matchAll(/"event"\s*:\s*"([^"]+)"/g)) {
      names.push(match[1]);
    }
  }
  return names;
}

test("PostHog sends $pageview and sound_play via /api/ingest", async ({ page }) => {
  const seen: string[] = [];

  await page.route(/\/(api\/)?ingest\//, async (route) => {
    const request = route.request();
    if (request.method() === "POST") {
      const buf = request.postDataBuffer();
      seen.push(...eventsFromPostBody(decodePostBody(buf)));
    }
    await route.continue();
  });

  await page.goto("/", { waitUntil: "domcontentloaded" });

  await expect.poll(() => seen.includes("$pageview"), { timeout: 15_000 }).toBe(true);

  const preview = page.getByRole("button", { name: /Preview/i }).first();
  await preview.click();

  await expect.poll(() => seen.includes("sound_play"), { timeout: 10_000 }).toBe(true);
});
