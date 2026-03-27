import { expect, test } from "@playwright/test";

import {
  buildTestUser,
  expectShellChrome,
  loginThroughUi,
  registerTestUser,
} from "../support/auth";
import { normalizeThemeSnapshot } from "../support/theme";

test.describe("flows/route-family-outcomes", () => {
  test("protects the dashboard, jobs, pipeline, settings, and targets route family", async ({
    page,
    request,
  }) => {
    const user = buildTestUser("route-family-outcomes");

    await registerTestUser(request, user);
    await loginThroughUi(page, user);
    await expectShellChrome(page);

    await expect(
      page.getByRole("main").getByRole("heading", { name: "Command Center", exact: true })
    ).toBeVisible();
    await expect(page.getByRole("button", { name: /^browse jobs$/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /^add application$/i })).toBeVisible();

    await page.getByRole("button", { name: /^browse jobs$/i }).click();
    await expect(page).toHaveURL(/\/jobs$/);
    await expect(
      page.getByRole("main").getByRole("heading", { name: "Jobs", exact: true })
    ).toBeVisible();
    await expect(page.getByRole("button", { name: /^exact$/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /^semantic$/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /^filters$/i })).toBeVisible();
    await expect(page.getByPlaceholder("Search jobs")).toBeVisible();
    await expect(page.getByText("No jobs found", { exact: true })).toBeVisible();

    await page.getByRole("button", { name: /^semantic$/i }).click();
    await expect(page.getByText("No semantic matches", { exact: true })).toBeVisible();

    await page.goto("/");
    await page.getByRole("button", { name: /^add application$/i }).click();
    await expect(page).toHaveURL(/\/pipeline$/);
    await expect(
      page.getByRole("main").getByRole("heading", { name: "Pipeline", exact: true })
    ).toBeVisible();
    await expect(page.getByRole("button", { name: /^auto-apply$/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /^copilot$/i })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Stages", exact: true })).toBeVisible();
    await expect(page.getByText("Saved", { exact: true })).toBeVisible();
    await expect(page.getByText("Applied", { exact: true })).toBeVisible();
    await expect(page.getByText("Select an application", { exact: true })).toBeVisible();

    await page.goto("/settings");
    await expect(
      page.getByRole("main").getByRole("heading", { name: "Settings", exact: true })
    ).toBeVisible();
    await page.getByRole("button", { name: /^appearance$/i }).click();
    await page.getByRole("button", { name: /^blueprint$/i }).click();
    await page.getByRole("button", { name: /^light$/i }).click();
    await page.getByRole("button", { name: /save changes/i }).click();

    await expect.poll(async () => page.evaluate(normalizeThemeSnapshot)).toMatchObject({
      themeFamily: "blueprint",
      dark: false,
      mode: "light",
      themeFamilyStored: "blueprint",
    });

    await page.goto("/targets");
    await expect(
      page.getByRole("main").getByRole("heading", { name: "Scrape Targets", exact: true })
    ).toBeVisible();
    await expect(page.getByRole("button", { name: /^run search sweep$/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /^run target batch$/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /^scraper log$/i })).toBeVisible();
    await expect(page.getByText("No targets found", { exact: true })).toBeVisible();

    const importTargetsButtons = page.getByRole("button", { name: /^import targets$/i });
    await expect(importTargetsButtons.first()).toBeVisible();
    await importTargetsButtons.first().click();
    await expect(page.getByRole("heading", { name: "Import Targets", exact: true })).toBeVisible();
    await page.getByRole("button", { name: /^cancel$/i }).click();
    await expect(page.getByRole("heading", { name: "Import Targets", exact: true })).toHaveCount(0);

    await page.getByRole("button", { name: /^scraper log$/i }).click();
    await expect(page.getByText("Live Scraper Log", { exact: true })).toBeVisible();
    await expect(page.getByText("Waiting for scraper events...", { exact: true })).toBeVisible();
  });
});
