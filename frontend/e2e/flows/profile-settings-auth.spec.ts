import { expect, test } from "@playwright/test";

import {
  buildTestUser,
  expectShellChrome,
  registerTestUser,
} from "../support/auth";

async function loginWithStableSubmit(
  page: import("@playwright/test").Page,
  user: { email: string; password: string }
) {
  await page.goto("/login");
  await expect(page.getByRole("heading", { name: /sign in/i })).toBeVisible();
  await page.getByLabel(/email address/i).fill(user.email);
  await page.getByLabel(/password/i).fill(user.password);
  await page.getByLabel(/password/i).press("Enter");
  await expect(page).toHaveURL(/\/$/);
}

test.describe("flows/profile-settings-auth", () => {
  test("keeps profile, settings, and auth roundtrip usable", async ({ page, request }) => {
    test.setTimeout(60_000);

    const user = buildTestUser("profile-settings-auth");

    await registerTestUser(request, user);
    await loginWithStableSubmit(page, user);
    await expectShellChrome(page);

    await page.goto("/profile");
    await expect(
      page.getByRole("main").getByRole("heading", { name: /profile ledger/i })
    ).toBeVisible();
    await expect(page.getByLabel("Email")).toHaveValue(user.email);
    await expect(page.getByLabel("Full name")).toBeVisible();
    await expect(page.getByLabel("Location")).toBeVisible();

    await page.goto("/settings");
    await expect(
      page.getByRole("main").getByRole("heading", { name: "Settings", exact: true })
    ).toBeVisible();
    await expect(page.getByRole("button", { name: /^appearance$/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /^integrations$/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /^data$/i })).toBeVisible();

    await page.getByRole("button", { name: /^integrations$/i }).click();
    await expect(page.getByText("OpenRouter", { exact: true })).toBeVisible();

    await page.getByRole("button", { name: /^data$/i }).click();
    await expect(page.getByRole("button", { name: /export data/i })).toBeVisible();

    await page.getByRole("button", { name: /logout/i }).click();
    await expect(page).toHaveURL(/\/login$/);
    await expect(page.getByRole("heading", { name: /^sign in$/i })).toBeVisible();

    await loginWithStableSubmit(page, user);
    await expect(page).toHaveURL(/\/$/);
    await expect(
      page.getByRole("main").getByRole("heading", { name: "Command Center", exact: true })
      ).toBeVisible();
  });
});
