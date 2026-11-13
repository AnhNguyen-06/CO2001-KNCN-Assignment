import { chromium, expect, test } from "@playwright/test";
import ExcelJS from "exceljs";
import path from "node:path";
import { spawnSync } from "node:child_process";
const name = "Nguyễn Văn Kiểm Thử";
const id = "0000456";
test("landing and workspace start without preloaded identities", async ({
  page,
  request,
}) => {
  expect((await (await request.get("/api/workspace")).json()).members).toEqual(
    [],
  );
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Presence.", exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Try recognition preview" }).click();
  await expect(page.getByText("Preview ready", { exact: true })).toBeVisible();
  await page.getByRole("link", { name: "Open workspace", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "Create attendance profile" }),
  ).toBeVisible();
  await expect(page.locator(".arrival-row")).toHaveCount(0);
  await page.screenshot({
    path: "test-results/clean-attendance.png",
    fullPage: true,
  });
  expect(errors).toEqual([]);
});
test("web enrollment, actual CV check-in, SQLite persistence and Excel work end to end", async ({
  page,
  request,
}, testInfo) => {
  await page.goto("/members");
  await expect(page.locator(".member-card")).toHaveCount(0);
  await page
    .getByRole("button", { name: "Register member", exact: true })
    .click();
  const dialog = page.getByRole("dialog");
  await dialog.getByLabel("Full name", { exact: true }).fill(name);
  await dialog.getByLabel("Member ID").fill(id);
  await dialog.getByRole("button", { name: "Continue", exact: true }).click();
  await dialog
    .getByRole("button", { name: "Turn on camera", exact: true })
    .click();
  await expect
    .poll(() =>
      dialog
        .locator("video")
        .evaluate((video: HTMLVideoElement) => video.readyState),
    )
    .toBeGreaterThan(1);
  for (let index = 1; index <= 3; index++) {
    await dialog
      .getByRole("button", { name: "Capture sample " + index, exact: true })
      .click();
    await expect(dialog.locator(".sample-slot.captured")).toHaveCount(index);
    await page.waitForTimeout(250);
  }
  await page.screenshot({ path: "test-results/web-enrollment.png" });
  await dialog.getByRole("button", { name: "Review profile" }).click();
  await dialog
    .getByRole("button", { name: "Save profile", exact: true })
    .click();
  await expect(dialog).toHaveCount(0);
  await expect(page.locator(".member-card")).toContainText(name);
  await page.getByRole("link", { name: "Attendance", exact: true }).click();
  await page
    .getByRole("button", { name: "Turn on camera", exact: true })
    .click();
  await expect(
    page.getByText("Attendance successful", { exact: true }),
  ).toBeVisible({ timeout: 30000 });
  await expect(page.locator(".arrival-row")).toHaveCount(1);
  await expect(page.locator(".face-overlay rect")).not.toHaveCount(0);
  await page.screenshot({
    path: "test-results/live-attendance.png",
    fullPage: true,
  });
  // Keep the real recognition stream running for a full minute: no extra rows.
  const stationaryUntil = Date.now() + 60_000;
  while (Date.now() < stationaryUntil) {
    await page.waitForTimeout(Math.min(10_000, stationaryUntil - Date.now()));
    const snapshot = await (await request.get("/api/workspace")).json();
    expect(snapshot.records).toHaveLength(1);
  }
  await page.evaluate(() => {
    (window as unknown as { testStream: MediaStream }).testStream = (
      document.querySelector("video") as HTMLVideoElement
    ).srcObject as MediaStream;
  });
  await page
    .getByRole("button", { name: "Turn off camera", exact: true })
    .click();
  await expect
    .poll(() =>
      page.evaluate(() =>
        (window as unknown as { testStream: MediaStream }).testStream
          .getTracks()
          .every((track) => track.readyState === "ended"),
      ),
    )
    .toBe(true);
  await page.evaluate(() => localStorage.clear());
  await page.reload();
  await expect(page.locator(".arrival-row")).toHaveCount(1);
  await page
    .getByRole("button", { name: "Turn on camera", exact: true })
    .click();
  await expect(
    page.getByText("Already checked in today", { exact: true }),
  ).toBeVisible();
  await expect(page.locator(".arrival-row")).toHaveCount(1);
  await page
    .getByRole("button", { name: "Turn off camera", exact: true })
    .click();
  await page.getByRole("link", { name: "Records", exact: true }).click();
  await page
    .getByRole("textbox", { name: "Search attendance records" })
    .fill(id);
  const downloadEvent = page.waitForEvent("download");
  await page.getByRole("button", { name: "Export Excel", exact: true }).click();
  const download = await downloadEvent;
  const workbook = new ExcelJS.Workbook();
  await workbook.xlsx.readFile((await download.path())!);
  const sheet = workbook.getWorksheet("Attendance")!;
  expect(sheet.rowCount).toBe(2);
  expect(sheet.getCell("B2").value).toBe(id);
  expect(sheet.getCell("C2").value).toBe(name);
  expect(sheet.getCell("F2").value).toBe("Present");
  const backend = path.resolve(process.cwd(), "../backend");
  const database = path.join(
    String(testInfo.config.metadata.backendDataDir),
    "attendance.sqlite3",
  );
  const counts = spawnSync(
    path.join(backend, ".venv/Scripts/python.exe"),
    [
      "-c",
      "import sqlite3,json,sys; c=sqlite3.connect(sys.argv[1]); print(json.dumps([c.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in ['persons','face_samples','attendance']]))",
      database,
    ],
    { encoding: "utf-8" },
  );
  expect(counts.status, counts.stderr).toBe(0);
  expect(JSON.parse(counts.stdout)).toEqual([1, 3, 1]);
  const workspace = await (await request.get("/api/workspace")).json();
  expect(workspace.members[0].id).toBe(id);
  expect(workspace.records[0].source).toBe("camera");
});
test("duplicate ID and old browser mock data do not create extra profiles", async ({
  page,
  request,
}) => {
  await page.addInitScript(() =>
    localStorage.setItem(
      "presence.frontend.v1",
      JSON.stringify({
        members: [{ id: "OLD-MOCK", name: "Old mock" }],
        records: [],
      }),
    ),
  );
  await page.goto("/members");
  await expect(page.locator(".member-card")).toHaveCount(1);
  await expect(page.getByText("Old mock", { exact: true })).toHaveCount(0);
  await expect
    .poll(() =>
      page.evaluate(() => localStorage.getItem("presence.frontend.v1")),
    )
    .toBeNull();
  await page
    .getByRole("button", { name: "Register member", exact: true })
    .click();
  const dialog = page.getByRole("dialog");
  await dialog.getByLabel("Full name", { exact: true }).fill("Another profile");
  await dialog.getByLabel("Member ID").fill(id);
  await dialog.getByRole("button", { name: "Continue", exact: true }).click();
  await expect(dialog.getByRole("alert")).toHaveText(
    "This member ID is already registered.",
  );
  await page.keyboard.press("Escape");
  expect(
    (await (await request.get("/api/workspace")).json()).members,
  ).toHaveLength(1);
});
test("unknown face remains unrecorded", async ({ request }) => {
  const browser = await chromium.launch({
    channel: "chrome",
    args: [
      "--use-fake-device-for-media-stream",
      "--use-fake-ui-for-media-stream",
      "--use-file-for-fake-video-capture=" +
        path.resolve(
          process.cwd(),
          "../backend/var/verification/web-camera-unknown.y4m",
        ),
    ],
  });
  try {
    const page = await browser.newPage({ baseURL: "http://127.0.0.1:3100" });
    await page.goto("/attendance");
    await page
      .getByRole("button", { name: "Turn on camera", exact: true })
      .click();
    await expect(
      page.getByText("Face not recognized", { exact: true }),
    ).toBeVisible({ timeout: 30000 });
    await page.waitForTimeout(1500);
    expect(
      (await (await request.get("/api/workspace")).json()).records,
    ).toHaveLength(1);
    await page
      .getByRole("button", { name: "Turn off camera", exact: true })
      .click();
  } finally {
    await browser.close();
  }
});
test("a frame without a face cannot be enrolled", async () => {
  const browser = await chromium.launch({
    channel: "chrome",
    args: [
      "--use-fake-device-for-media-stream",
      "--use-fake-ui-for-media-stream",
      "--use-file-for-fake-video-capture=" +
        path.resolve(
          process.cwd(),
          "../backend/var/verification/web-camera-empty.y4m",
        ),
    ],
  });
  try {
    const page = await browser.newPage({ baseURL: "http://127.0.0.1:3100" });
    await page.goto("/members?register=true");
    const dialog = page.getByRole("dialog");
    await dialog
      .getByLabel("Full name", { exact: true })
      .fill("Rejected profile");
    await dialog.getByLabel("Member ID").fill("REJECTED");
    await dialog.getByRole("button", { name: "Continue", exact: true }).click();
    await dialog
      .getByRole("button", { name: "Turn on camera", exact: true })
      .click();
    await expect
      .poll(() =>
        dialog
          .locator("video")
          .evaluate((video: HTMLVideoElement) => video.readyState),
      )
      .toBeGreaterThan(1);
    await dialog
      .getByRole("button", { name: "Capture sample 1", exact: true })
      .click();
    await expect(dialog.getByRole("alert")).toContainText("No face detected");
    await expect(dialog.locator(".sample-slot.captured")).toHaveCount(0);
    await page.keyboard.press("Escape");
  } finally {
    await browser.close();
  }
});
test("camera denial and backend failure have recoverable UI states", async ({
  page,
}) => {
  await page.addInitScript(() => {
    navigator.mediaDevices.getUserMedia = async () => {
      throw new DOMException("Denied", "NotAllowedError");
    };
  });
  await page.goto("/attendance");
  await page
    .getByRole("button", { name: "Turn on camera", exact: true })
    .click();
  await expect(
    page.getByText(
      "Camera permission was denied. Allow access in your browser, then retry.",
    ),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Turn off camera", exact: true })
    .click();
  await page.route("**/api/workspace", (route) =>
    route.fulfill({
      status: 503,
      contentType: "application/json",
      body: JSON.stringify({
        message: "Recognition service temporarily unavailable",
        code: "BACKEND_UNAVAILABLE",
      }),
    }),
  );
  await page.reload();
  await expect(page.locator(".storage-warning")).toContainText(
    "Recognition service temporarily unavailable",
  );
  await expect(
    page.getByRole("button", { name: "Turn on camera", exact: true }),
  ).toBeDisabled();
  await page.unroute("**/api/workspace");
  await page
    .getByRole("button", { name: "Retry connection", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Turn on camera", exact: true }),
  ).toBeEnabled();
  const snapshot = await (await page.request.get("/api/workspace")).json();
  await page.route("**/api/workspace", (route) =>
    route.fulfill({
      json: {
        ...snapshot,
        exports: snapshot.exports.map((state: object) => ({
          ...state,
          status: "error",
        })),
      },
    }),
  );
  await page.route("**/api/exports/retry", (route) =>
    route.fulfill({
      status: 503,
      json: {
        code: "BACKEND_UNAVAILABLE",
        message: "Excel retry temporarily unavailable",
      },
    }),
  );
  await expect(
    page.getByRole("button", { name: "Retry Excel update" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Retry Excel update" }).click();
  await expect(
    page.getByText("Excel retry temporarily unavailable", { exact: true }),
  ).toBeVisible();
});
test("preference reset keeps database accounts and attendance intact", async ({
  page,
  request,
}) => {
  await page.goto("/settings");
  const motion = page.getByRole("switch", { name: "Reduce ambient motion" });
  await motion.click();
  await page.reload();
  await expect(motion).toHaveAttribute("aria-checked", "true");
  await page
    .getByRole("button", { name: "Reset preferences", exact: true })
    .click();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Reset preferences", exact: true })
    .click();
  await expect(motion).toHaveAttribute("aria-checked", "false");
  const data = await (await request.get("/api/workspace")).json();
  expect(data.members).toHaveLength(1);
  expect(data.records).toHaveLength(1);
});
test("connected pages are responsive and keyboard navigation remains available", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.setViewportSize({ width: 390, height: 844 });
  for (const route of [
    "/",
    "/attendance",
    "/members",
    "/records",
    "/settings",
  ]) {
    await page.goto(route);
    await page.waitForTimeout(300);
    expect(
      await page.evaluate(() => document.documentElement.scrollWidth),
    ).toBeLessThanOrEqual(390);
    await page.screenshot({
      path:
        "test-results/" +
        (route === "/" ? "landing" : route.slice(1)) +
        "-mobile.png",
      fullPage: true,
    });
  }
  await page.getByRole("button", { name: "Open navigation" }).click();
  await page.getByRole("link", { name: "Attendance", exact: true }).click();
  await expect(page).toHaveURL(/attendance$/);
  expect(errors).toEqual([]);
});
