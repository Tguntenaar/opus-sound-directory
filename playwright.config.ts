import { defineConfig, devices } from "@playwright/test";

const port = 43125;

export default defineConfig({
  testDir: "tests",
  timeout: 60_000,
  fullyParallel: false,
  workers: 1,
  use: {
    ...devices["Desktop Chrome"],
    baseURL: `http://127.0.0.1:${port}`,
  },
  webServer: process.env.PLAYWRIGHT_REUSE_SERVER
    ? undefined
    : {
        command: `bash scripts/posthog-e2e-server.sh`,
        url: `http://127.0.0.1:${port}`,
        reuseExistingServer: false,
        timeout: 240_000,
        env: {
          NEXT_PUBLIC_POSTHOG_KEY: "phc_playwright_test_key",
          PLAYWRIGHT_NODE: process.env.PLAYWRIGHT_NODE ?? process.execPath,
          PLAYWRIGHT_PORT: String(port),
        },
      },
});
