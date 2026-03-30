import { expect, test } from "@playwright/test";

import { buildTestUser, loginThroughUi, registerTestUser } from "../support/auth";

test.describe("flows/communications-setup", () => {
  test("keeps networking, email, and onboarding usable on a fresh account", async ({
    page,
    request,
  }) => {
    test.setTimeout(60_000);

    const user = buildTestUser("communications-setup");

    await registerTestUser(request, user);
    await loginThroughUi(page, user);

    await page.goto("/networking");
    await expect(
      page.getByRole("main").getByRole("heading", { name: "Networking", exact: true })
    ).toBeVisible();
    await expect(page.getByRole("button", { name: /^new contact$/i })).toBeVisible();
    await expect(page.getByText("Contacts", { exact: true }).first()).toBeVisible();
    await expect(page.getByRole("button", { name: /^create contact$/i })).toBeVisible();
    await expect(page.getByText("No referral requests yet", { exact: true })).toBeVisible();

    await page.goto("/email");
    await expect(
      page.getByRole("main").getByRole("heading", { name: "Email Signals", exact: true })
    ).toBeVisible();
    await expect(page.getByText("Signal log", { exact: true })).toBeVisible();
    await expect(page.getByText("Choose a log entry", { exact: true })).toBeVisible();
    await expect(page.getByRole("button", { name: /^process signal$/i })).toBeVisible();
    await expect(page.getByText("Scope", { exact: true })).toBeVisible();

    await page.goto("/onboarding");
    await expect(page.getByRole("heading", { name: "Onboarding", exact: true })).toBeVisible();
    await expect(page.getByText("What gets configured", { exact: true })).toBeVisible();
    await expect(page.getByRole("button", { name: /^next$/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /skip for now/i })).toBeVisible();
  });
});
