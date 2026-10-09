import { test, expect } from "@playwright/test";

if (process.env.SEARCH_TEST_BASE_URL) test.use({ baseURL: process.env.SEARCH_TEST_BASE_URL });

test("search opens from every page, traps focus, and restores it on Escape", async ({ page }) => {
  for (const path of ["/", "/about", "/e/ui-success-chime"]) {
    await page.goto(path);
    const trigger = page.getByRole("button", { name: "Search all sounds" });
    await expect(trigger).toBeEnabled();
    await trigger.focus();
    await page.keyboard.press("Control+k");
    const dialog = page.getByRole("dialog", { name: "Search all sounds" });
    await expect(dialog).toBeVisible();
    await expect(page.getByRole("combobox")).toBeFocused();
    await page.keyboard.press("Shift+Tab");
    await expect(dialog.getByRole("button", { name: "Close search" })).toBeFocused();
    await page.keyboard.press("Escape");
    await expect(dialog).not.toBeVisible();
    await expect(trigger).toBeFocused();
    await page.keyboard.press("Meta+k");
    await expect(dialog).toBeVisible();
    await page.keyboard.press("Meta+k");
    await expect(dialog).not.toBeVisible();
  }
});

test("queries are debounced, results support arrow keys and Enter", async ({ page }) => {
  const queries: string[] = [];
  await page.route("**/api/search?*", async (route) => {
    queries.push(new URL(route.request().url()).searchParams.get("q")!);
    await route.fulfill({ json: { provider: "algolia", nbHits: 2, hits: [
      { objectID: "first", slug: "ui-success-chime", title: "Success chime", category: "ui", durationSec: 1 },
      { objectID: "second", slug: "game-coin-pickup", title: "Coin pickup", category: "game", durationSec: 0.5 },
    ] } });
  });
  await page.goto("/about");
  await page.getByRole("button", { name: "Search all sounds" }).click();
  await page.getByRole("combobox").pressSequentially("chime", { delay: 30 });
  await expect(page.getByRole("row")).toHaveCount(2);
  expect(queries).toEqual(["chime"]);
  await expect(page.getByText("Search by Algolia")).toBeVisible();
  await page.keyboard.press("ArrowDown");
  await expect(page.getByRole("row", { name: /Coin pickup/ })).toHaveAttribute("aria-selected", "true");
  await page.keyboard.press("Enter");
  await expect(page).toHaveURL(/\/e\/game-coin-pickup$/);
  await expect(page.getByRole("dialog")).not.toBeVisible();
});

test("empty results, retry, and mobile header remain usable", async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 812 });
  let fail = true;
  await page.route("**/api/search?*", async (route) => {
    if (fail) await route.fulfill({ status: 503, json: { error: "Unavailable" } });
    else await route.fulfill({ json: { hits: [], nbHits: 0, provider: "algolia" } });
  });
  await page.goto("/about");
  await page.getByRole("button", { name: "Search all sounds" }).click();
  await page.getByRole("combobox").fill("unknown");
  await expect(page.getByRole("status")).toHaveText("Search is unavailable. Try again.");
  fail = false;
  await page.getByRole("button", { name: "Try again", exact: true }).click();
  await expect(page.getByRole("status")).toHaveText("No sounds found. Try another word.");
  const box = await page.getByRole("dialog").boundingBox();
  expect(box!.x).toBeGreaterThanOrEqual(0);
  expect(box!.x + box!.width).toBeLessThanOrEqual(375);
});

test("public search feed excludes hidden sounds and API rejects invalid queries", async ({ request }) => {
  const feed = await request.get("/api/search/catalog");
  expect(feed.ok()).toBeTruthy();
  const { records } = await feed.json();
  expect(records.length).toBeGreaterThan(0);
  expect(records.some((record: { slug: string }) => record.slug === "ui-camera-shutter")).toBeFalsy();
  expect((await request.get("/api/search?q=a")).status()).toBe(400);
  expect((await request.get(`/api/search?q=${"a".repeat(201)}`)).status()).toBe(400);
  const search = await request.get("/api/search?q=success%20chime");
  expect(search.ok()).toBeTruthy();
  expect((await search.json()).hits.some((hit: { slug: string }) => hit.slug === "ui-success-chime")).toBeTruthy();
});

test("search previews play, pause, replace each other, and stop when search changes or closes", async ({ page, request }) => {
  const { records } = await (await request.get("/api/search/catalog")).json();
  const hits = ["ambient-bed-lofi", "podcast-intro-10s"].map(slug => records.find((record: { slug: string }) => record.slug === slug));
  expect(hits.every(hit => hit?.previewUrl)).toBeTruthy();
  await page.route("**/api/search?*", route => route.fulfill({ json: { provider: "algolia", nbHits: hits.length, hits } }));
  await page.goto("/about");
  await page.getByRole("button", { name: "Search all sounds" }).click();
  await page.getByRole("combobox").fill("ambient");
  const first = page.getByRole("button", { name: `Preview ${hits[0].title}`, exact: true });
  await expect(first).toBeVisible();
  expect(await page.locator("audio[data-search-preview]").evaluateAll(elements => elements.every(element => (element as HTMLAudioElement).paused && (element as HTMLAudioElement).preload === "none"))).toBeTruthy();
  await first.click();
  await expect(page.getByRole("button", { name: `Pause ${hits[0].title}`, exact: true })).toBeVisible();
  await expect(page.getByRole("dialog")).toBeVisible();
  await page.getByRole("button", { name: `Preview ${hits[1].title}`, exact: true }).click();
  await expect(page.getByRole("button", { name: `Pause ${hits[1].title}`, exact: true })).toBeVisible();
  await expect(first).toBeVisible();
  expect(await page.locator("audio[data-search-preview]").evaluateAll(elements => elements.filter(element => !(element as HTMLAudioElement).paused).length)).toBe(1);
  await page.getByRole("button", { name: `Pause ${hits[1].title}`, exact: true }).click();
  expect(await page.locator("audio[data-search-preview]").evaluateAll(elements => elements.every(element => (element as HTMLAudioElement).paused))).toBeTruthy();
  await first.click();
  const playing = await page.locator('audio[data-search-preview="ambient-bed-lofi"]').elementHandle();
  await page.getByRole("combobox").fill("other");
  await expect.poll(() => playing!.evaluate(element => (element as HTMLAudioElement).paused)).toBeTruthy();
  await page.getByRole("button", { name: `Preview ${hits[0].title}`, exact: true }).click();
  const last = await page.locator('audio[data-search-preview="ambient-bed-lofi"]').elementHandle();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).not.toBeVisible();
  expect(await last!.evaluate(element => (element as HTMLAudioElement).paused)).toBeTruthy();
});

test("broken preview can be retried without navigating away", async ({ page, request }) => {
  const { records } = await (await request.get("/api/search/catalog")).json();
  const hit = { ...records[0], previewUrl: "/missing-search-preview.mp3" };
  await page.route("**/api/search?*", route => route.fulfill({ json: { hits: [hit], nbHits: 1, provider: "algolia" } }));
  await page.route("**/missing-search-preview.mp3", route => route.fulfill({ status: 404, body: "Missing" }));
  await page.goto("/about");
  await page.getByRole("button", { name: "Search all sounds" }).click();
  await page.getByRole("combobox").fill("broken");
  await page.getByRole("button", { name: `Preview ${hit.title}`, exact: true }).click();
  await expect(page.getByRole("button", { name: `Retry preview for ${hit.title}` })).toBeVisible();
  await expect(page.getByRole("dialog")).toBeVisible();
  await expect(page).toHaveURL(/\/about$/);
});
