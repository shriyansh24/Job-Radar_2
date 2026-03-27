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

test.describe("flows/prepare-intelligence-outcomes", () => {
  test("keeps prepare and intelligence routes usable on a fresh account", async ({
    page,
    request,
  }) => {
    test.setTimeout(60_000);

    const user = buildTestUser("prepare-intelligence");

    await registerTestUser(request, user);
    await loginWithStableSubmit(page, user);

    await page.goto("/copilot");
    await expect(
      page.getByRole("main").getByRole("heading", { name: "Copilot", exact: true })
    ).toBeVisible();
    await expect(page.getByRole("button", { name: /^assistant$/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /^history$/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /^letters$/i })).toBeVisible();
    await expect(page.getByText("Start a chat", { exact: true })).toBeVisible();

    await page.goto("/resume");
    await expect(
      page.getByRole("main").getByRole("heading", { name: "Resume Builder", exact: true })
    ).toBeVisible();
    await expect(page.getByRole("button", { name: /^upload$/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /^versions$/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /^tailor$/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /^council$/i })).toBeVisible();
    await expect(page.getByText(/drag and drop a resume/i)).toBeVisible();

    await page.goto("/interview");
    await expect(
      page.getByRole("main").getByRole("heading", { name: "Interview Prep", exact: true })
    ).toBeVisible();
    await expect(page.getByRole("button", { name: /^practice$/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /^history$/i })).toBeVisible();
    await expect(page.getByText("No active session", { exact: true })).toBeVisible();

    await page.getByRole("button", { name: /^history$/i }).click();
    await expect(page.getByRole("main")).toContainText(/No sessions yet|Session /);

    await page.goto("/salary");
    await expect(
      page.getByRole("main").getByRole("heading", { name: "Salary Insights", exact: true })
    ).toBeVisible();
    await expect(page.getByPlaceholder("Senior Frontend Engineer")).toBeVisible();
    await expect(page.getByRole("button", { name: /^research$/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /^evaluate$/i })).toBeVisible();

    await page.goto("/vault");
    await expect(
      page.getByRole("main").getByRole("heading", { name: "Document Vault", exact: true })
    ).toBeVisible();
    await expect(page.getByRole("button", { name: /^resumes$/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /^cover letters$/i })).toBeVisible();
    await expect(page.getByText("No resumes", { exact: true })).toBeVisible();

    await page.getByRole("button", { name: /^cover letters$/i }).click();
    await expect(page.getByText("No cover letters", { exact: true })).toBeVisible();

    await page.goto("/analytics");
    await expect(
      page.getByRole("main").getByRole("heading", { name: "Analytics", exact: true })
    ).toBeVisible();
    await expect(page.getByRole("button", { name: /last 30 days/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /export pdf/i })).toBeVisible();

    await page.goto("/outcomes");
    await expect(
      page.getByRole("main").getByRole("heading", { name: "Outcomes", exact: true })
    ).toBeVisible();
    await expect(page.getByRole("button", { name: /^save outcome$/i })).toBeVisible();
    await expect(page.getByText("Company insight lookup", { exact: true })).toBeVisible();
    await expect(page.getByText("No company insight selected", { exact: true })).toBeVisible();
  });
});
