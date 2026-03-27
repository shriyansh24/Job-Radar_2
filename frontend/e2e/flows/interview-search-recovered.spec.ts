import { expect, test } from "@playwright/test";

import {
  buildTestUser,
  expectShellChrome,
  loginThroughUi,
  registerTestUser,
} from "../support/auth";

test.describe("flows/interview-search-recovered", () => {
  test("keeps recovered interview prep and semantic search handoff usable", async ({
    page,
    request,
  }) => {
    test.setTimeout(60_000);

    const user = buildTestUser("interview-search-recovered");

    await registerTestUser(request, user);
    await loginThroughUi(page, user);
    await expectShellChrome(page);

    await page.goto("/interview");
    await expect(
      page.getByRole("main").getByRole("heading", { name: "Interview Prep", exact: true })
    ).toBeVisible();
    await page.getByRole("button", { name: /^prepare$/i }).click();
    await expect(page.getByText("Prepare interview bundle", { exact: true })).toBeVisible();
    await expect(page.getByLabel(/resume text/i)).toBeVisible();
    await expect(page.getByRole("button", { name: /^generate bundle$/i })).toBeDisabled();

    await page.goto("/jobs?mode=semantic&q=frontend%20engineer");
    await expect(
      page.getByRole("main").getByRole("heading", { name: "Jobs", exact: true })
    ).toBeVisible();
    await expect(page.getByRole("button", { name: /^semantic$/i })).toBeVisible();
    await expect(
      page.getByPlaceholder("Describe a role, company, or stack")
    ).toHaveValue("frontend engineer");

    await page.goto("/search-expansion");
    await expect(
      page.getByRole("main").getByRole("heading", { name: "Search Expansion", exact: true })
    ).toBeVisible();
    await page.getByPlaceholder("senior frontend engineer").fill("frontend engineer");
    await page.getByRole("button", { name: /^expand query$/i }).first().click();
    await expect(page.getByText("Original query", { exact: true })).toBeVisible();

    await page.getByRole("button", { name: /^open in jobs$/i }).click();
    await expect(page).toHaveURL(/\/jobs\?mode=semantic&q=frontend%20engineer/);
    await expect(
      page.getByPlaceholder("Describe a role, company, or stack")
    ).toHaveValue("frontend engineer");
  });
});
