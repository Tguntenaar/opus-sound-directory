import { test as base, expect } from "@playwright/test";

/** Context fixture runs before `page`; init script applies to every navigation. */
export const test = base.extend({
  context: async ({ context }, use) => {
    await context.addInitScript(() => {
      Object.defineProperty(navigator, "webdriver", {
        get: () => false,
        configurable: true,
      });
    });
    await use(context);
  },
});

export { expect };
