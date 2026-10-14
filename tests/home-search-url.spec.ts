import { test, expect } from "@playwright/test";

test("?q= pre-fills the home search box and filters the grid on load", async ({ page }) => {
  await page.goto("/");
  const unfilteredStatus = await page.getByRole("status").textContent();

  await page.goto("/?q=guitar");
  await expect(page.getByRole("searchbox", { name: "Search sounds" })).toHaveValue("guitar");

  const cards = page.locator("[data-sound-card]");
  await expect(cards.first()).toBeVisible();
  const filteredCount = await cards.count();
  expect(filteredCount).toBeGreaterThan(0);

  const filteredStatus = await page.getByRole("status").textContent();
  expect(filteredStatus).not.toBe(unfilteredStatus);
  expect(filteredStatus).toMatch(new RegExp(`\\b${filteredCount} of ${filteredCount} sounds`));
});

test("home search keeps ?q= in the URL via replaceState", async ({ page }) => {
  await page.goto("/");
  const search = page.getByRole("searchbox", { name: "Search sounds" });
  await expect(search).toBeVisible();
  await search.fill("guitar");
  await expect(search).toHaveValue("guitar");
  await expect(page).toHaveURL(/\?q=guitar/, { timeout: 5_000 });

  await search.fill("");
  await expect(search).toHaveValue("");
  await expect(page).toHaveURL(/\/$/, { timeout: 5_000 });
});

test("WebSite JSON-LD exposes SearchAction for ?q=", async ({ page }) => {
  await page.goto("/");
  const scripts = await page.locator('script[type="application/ld+json"]').allTextContents();
  const graphs = scripts.map((raw) => JSON.parse(raw) as Record<string, unknown>);
  const website = graphs.find((item) => item["@type"] === "WebSite");
  expect(website).toBeTruthy();
  const action = website!.potentialAction as {
    target?: { urlTemplate?: string };
  };
  expect(action?.target?.urlTemplate).toMatch(/\?q=\{search_term_string\}$/);
});
