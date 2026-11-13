import { defineConfig } from "@playwright/test";
import { mkdirSync, mkdtempSync } from "node:fs";
import path from "node:path";
const backend = path.resolve(process.cwd(), "../backend");
mkdirSync(path.join(backend, "var"), { recursive: true });
const dataDir =
  process.env.PRESENCE_TEST_DATA_DIR ??
  mkdtempSync(path.join(backend, "var", "web-e2e-"));
process.env.PRESENCE_TEST_DATA_DIR = dataDir;
const knownVideo = path.join(backend, "var/verification/web-camera-known.y4m");
const externalBackend = process.env.PRESENCE_E2E_BACKEND_URL;
export default defineConfig({
  testDir: "./tests",
  fullyParallel: false,
  workers: 1,
  timeout: 180000,
  expect: { timeout: 20000 },
  reporter: "list",
  metadata: { backendDataDir: dataDir },
  use: {
    baseURL: "http://127.0.0.1:3100",
    channel: "chrome",
    viewport: { width: 1440, height: 1000 },
    launchOptions: {
      args: [
        "--use-fake-device-for-media-stream",
        "--use-fake-ui-for-media-stream",
        "--use-file-for-fake-video-capture=" + knownVideo,
      ],
    },
    screenshot: "only-on-failure",
    trace: "off",
  },
  webServer: [
    ...(!externalBackend
      ? [
          {
            command:
              '"' +
              path.join(backend, ".venv/Scripts/python.exe") +
              '" -m uvicorn presence_cv.api:app --host 127.0.0.1 --port 8001',
            cwd: backend,
            url: "http://127.0.0.1:8001/api/health",
            reuseExistingServer: false,
            timeout: 60000,
            env: {
              PRESENCE_DATA_DIR: dataDir,
              PRESENCE_BACKEND_KEY: "",
              DATABASE_URL: " ",
              PRESENCE_EXPORT_MODE: "daily",
            },
          },
        ]
      : []),
    {
      command: "npm run start -- --port 3100",
      url: "http://127.0.0.1:3100/api/health",
      reuseExistingServer: false,
      timeout: 60000,
      env: {
        PRESENCE_BACKEND_URL: externalBackend ?? "http://127.0.0.1:8001",
        PRESENCE_BACKEND_KEY: process.env.PRESENCE_E2E_BACKEND_KEY ?? "",
      },
    },
  ],
});
