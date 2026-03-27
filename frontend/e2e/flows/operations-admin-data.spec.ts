import { expect, test } from "@playwright/test";

import { buildTestUser, registerTestUser } from "../support/auth";

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

test.describe("flows/operations-admin-data", () => {
  test("keeps operations data and admin routes stable", async ({ page, request }) => {
    test.setTimeout(60_000);

    const user = buildTestUser("operations-admin-data");

    await registerTestUser(request, user);
    await loginWithStableSubmit(page, user);

    await page.goto("/admin");
    await expect(
      page.getByRole("main").getByRole("heading", { name: "Admin", exact: true })
    ).toBeVisible();
    await expect(page.getByRole("button", { name: /^reindex fts$/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /^reindex search$/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /^export data$/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /^import data$/i })).toBeVisible();
    await expect(page.getByText("Source health", { exact: true })).toBeVisible();

    await page.goto("/sources");
    await expect(
      page.getByRole("main").getByRole("heading", { name: "Source Health", exact: true })
    ).toBeVisible();
    await expect(page.getByText(/sources$/i).first()).toBeVisible();

    await page.goto("/companies");
    await expect(
      page.getByRole("main").getByRole("heading", { name: "Companies", exact: true })
    ).toBeVisible();
    await expect(page.getByRole("button", { name: /^all$/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /^verified$/i })).toBeVisible();

    await page.goto("/canonical-jobs");
    await expect(
      page.getByRole("main").getByRole("heading", { name: "Canonical Jobs", exact: true })
    ).toBeVisible();
    await expect(page.getByRole("button", { name: /show stale/i })).toBeVisible();

    await page.goto("/search-expansion");
    await expect(
      page.getByRole("main").getByRole("heading", { name: "Search Expansion", exact: true })
    ).toBeVisible();
    await expect(page.getByPlaceholder("senior frontend engineer")).toBeVisible();
    await expect(page.getByRole("button", { name: /^expand query$/i }).first()).toBeVisible();
    await expect(page.getByText("No expansion run yet", { exact: true })).toBeVisible();
  });
});
