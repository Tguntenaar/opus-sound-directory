import { test, expect } from "./fixtures";

for (const provider of ["github", "google"] as const) {
  for (const outcome of ["returned", "failed"] as const) {
    test(`${provider} sign-in records ${outcome} on the collapsed submit page exactly once`, async ({ page, context }) => {
      await context.addInitScript(() => {
        let posthog: unknown;
        Object.defineProperty(window, "posthog", {
          configurable: true,
          get: () => posthog,
          set: (value: { capture: (...args: unknown[]) => unknown }) => {
            posthog = value;
            const capture = value.capture.bind(value);
            value.capture = (...args: unknown[]) => {
              if (typeof args[0] === "string" && args[0].startsWith("auth_sign_in_")) {
                const events = JSON.parse(sessionStorage.getItem("test:auth-events") || "[]");
                events.push({ event: args[0], properties: args[1] });
                sessionStorage.setItem("test:auth-events", JSON.stringify(events));
              }
              return capture(...args);
            };
          },
        });
      });
      let signedIn = false;
      await page.route("**/api/account", route => route.fulfill({ json: {
        providers: ["github", "google"],
        user: signedIn ? { id: "test-user", name: "Test", email: "test@example.test", emailVerified: true } : null,
      } }));
      await page.route("**/api/auth/sign-in/social", async route => {
        const body = route.request().postDataJSON();
        expect(body.provider).toBe(provider);
        expect(body.disableRedirect).toBe(true);
        expect(body.callbackURL).toBe("/submit?sign_in=returned");
        expect(body.errorCallbackURL).toBe("/submit?sign_in=failed");
        signedIn = outcome === "returned";
        await route.fulfill({ json: { url: `${new URL(route.request().url()).origin}/submit?sign_in=${outcome}`, redirect: false } });
      });
      await page.goto("/submit", { waitUntil: "domcontentloaded" });
      await page.getByText("Or submit manually", { exact: true }).click();
      await page.waitForFunction(() => !!(window as unknown as { posthog?: unknown }).posthog);
      await page.getByRole("button", { name: `Continue with ${provider === "github" ? "GitHub" : "Google"}` }).click();
      await page.waitForURL("**/submit");
      const events = () => page.evaluate(() => JSON.parse(sessionStorage.getItem("test:auth-events") || "[]") as { event: string; properties: { provider: string } }[]);
      const expected = outcome === "returned" ? "auth_sign_in_succeeded" : "auth_sign_in_failed";
      await expect.poll(async () => (await events()).map(event => event.event)).toEqual([
        "auth_sign_in_clicked", "auth_sign_in_started", expected,
      ]);
      expect((await events()).every(event => event.properties.provider === provider)).toBe(true);
      await expect(page.getByRole("heading", { name: "Sign in to contribute" })).toHaveCount(0);
      await page.reload({ waitUntil: "domcontentloaded" });
      await expect(page.getByRole("heading", { name: "Add your sound" })).toBeVisible();
      expect((await events()).filter(event => event.event === expected)).toHaveLength(1);
    });
  }
}
