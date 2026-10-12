import { defineConfig } from "@playwright/test";

// Requer backend (:8000) e frontend (:3000) já no ar, com banco DESCARTÁVEL.
// Nunca aponte para a base de homologação real: o teste cria registros.
export default defineConfig({
  testDir: "./tests",
  timeout: 90_000,
  retries: process.env.CI ? 1 : 0,
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://127.0.0.1:3000",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
});
