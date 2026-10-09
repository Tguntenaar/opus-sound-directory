import { test, expect } from "./fixtures";

test("manual submission measures intent, validation and server outcomes without form contents", async ({ page }) => {
  await page.route("**/api/account", (route) => route.fulfill({
    json: { user: { emailVerified: true } },
  }));
  let attempts = 0;
  await page.route("**/api/submit", (route) => {
    attempts++;
    return route.fulfill(attempts === 1
      ? { status: 503, json: { error: "Try again" } }
      : { json: { ok: true, status: "pending_review" } });
  });
  await page.goto("/submit");
  await page.waitForFunction(() => Boolean((window as unknown as { posthog?: unknown }).posthog));
  await page.evaluate(() => {
    const target = window as unknown as {
      posthog: { capture: (event: string, properties?: unknown) => unknown };
      submissionEvents: Array<{ event: string; properties?: unknown }>;
    };
    target.submissionEvents = [];
    const original = target.posthog.capture.bind(target.posthog);
    target.posthog.capture = (event, properties) => {
      target.submissionEvents.push({ event, properties });
      return original(event, properties);
    };
  });
  await page.getByText("Or submit manually", { exact: true }).click();
  await page.getByLabel("Title", { exact: true }).fill("Private draft title");
  await page.getByLabel("Prompt", { exact: true }).fill("A private draft prompt with enough characters to pass the submission validation.");
  await page.getByRole("button", { name: "Submit sound", exact: true }).click();
  await expect(page.getByRole("alert")).toHaveText("Select at least one mood");
  await page.locator("fieldset button").first().click();
  await page.getByRole("button", { name: "Submit sound", exact: true }).click();
  await expect(page.getByRole("alert")).toHaveText("Try again");
  await page.getByRole("button", { name: "Submit sound", exact: true }).click();
  await expect(page.getByText("Thanks — we got your submission.")).toBeVisible();
  const events = await page.evaluate(() => (window as unknown as {
    submissionEvents: Array<{ event: string; properties?: Record<string, unknown> }>;
  }).submissionEvents.filter(({ event }) => event.startsWith("submit_")));
  expect(events.map(({ event }) => event)).toEqual([
    "submit_manual_open", "submit_form_access", "submit_form_start",
    "submit_form_attempt", "submit_form_validation_error",
    "submit_form_attempt", "submit_form_error", "submit_form_attempt", "submit_form_submit",
  ]);
  expect(events.find(({ event }) => event === "submit_form_error")?.properties).toMatchObject({ http_status: 503 });
  expect(JSON.stringify(events)).not.toContain("Private draft");
  expect(JSON.stringify(events)).not.toContain("private draft prompt");
});
