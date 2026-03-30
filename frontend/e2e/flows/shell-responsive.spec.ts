import { expect, test, type APIRequestContext, type Page } from "@playwright/test";

import { buildTestUser, loginThroughUi, registerTestUser } from "../support/auth";

async function loginAndOpenTargets(page: Page, request: APIRequestContext, suffix: string) {
  const user = buildTestUser(suffix);
  await registerTestUser(request, user);
  await loginThroughUi(page, user);
  await page.goto("/targets");
  await expect(
    page.getByRole("main").getByRole("heading", {
      name: "Scrape Targets",
      exact: true,
    })
  ).toBeVisible();
}

test.describe("flows/shell-responsive", () => {
  test.describe.configure({ mode: "serial" });

  test("desktop keeps the sidebar rail mounted and bottom nav absent", async ({
    page,
    request,
  }) => {
    test.setTimeout(60_000);
    await page.setViewportSize({ width: 1440, height: 960 });
    await loginAndOpenTargets(page, request, "shell-desktop");

    await expect(page.getByRole("button", { name: /collapse navigation/i })).toBeVisible();
    await expect(
      page.getByRole("complementary").getByRole("heading", { name: "JobRadar", exact: true })
    ).toBeVisible();
    await expect(page.getByRole("button", { name: /open navigation/i })).toBeHidden();
    await expect(page.getByRole("link", { name: /^Radar$/i })).toHaveCount(0);
  });

  test("tablet uses the drawer toggle while keeping bottom nav available", async ({
    page,
    request,
  }) => {
    test.setTimeout(60_000);
    await page.setViewportSize({ width: 900, height: 1200 });
    await loginAndOpenTargets(page, request, "shell-tablet");

    await expect(page.getByRole("button", { name: /open navigation/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /collapse navigation/i })).toBeHidden();
    await expect(page.getByRole("link", { name: /^Radar$/i })).toBeVisible();

    await page.getByRole("button", { name: /open navigation/i }).click();
    await expect(page.getByRole("button", { name: /close navigation/i })).toBeVisible();

    await page.getByRole("button", { name: /close navigation/i }).click();
    await expect(page.getByRole("button", { name: /close navigation/i })).toBeHidden();
    await expect(page.getByRole("link", { name: /^Radar$/i })).toBeVisible();
    await expect(
      page.getByRole("main").getByRole("heading", { name: "Scrape Targets", exact: true })
    ).toBeVisible();
  });

  test("phone keeps the drawer and bottom nav usable together", async ({
    page,
    request,
  }) => {
    test.setTimeout(60_000);
    await page.setViewportSize({ width: 390, height: 844 });
    await loginAndOpenTargets(page, request, "shell-phone");

    await expect(page.getByRole("button", { name: /open navigation/i })).toBeVisible();
    await expect(page.getByRole("link", { name: /^Radar$/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /scraper log/i })).toBeVisible();

    await page.getByRole("button", { name: /open navigation/i }).click();
    await expect(page.getByRole("button", { name: /close navigation/i })).toBeVisible();
    await page.getByRole("button", { name: /close navigation/i }).click();
    await expect(page.getByRole("button", { name: /close navigation/i })).toBeHidden();

    await page.getByRole("link", { name: /^Radar$/i }).click();
    await expect(page).toHaveURL(/\/$/);
    await expect(
      page.getByRole("main").getByRole("heading", { name: "Command Center", exact: true })
    ).toBeVisible();
  });
});
