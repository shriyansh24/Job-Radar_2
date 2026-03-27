import { expect, test } from "@playwright/test";

import { buildTestUser, loginThroughUi, registerTestUser } from "../support/auth";

test.describe("flows/resume-template-preview", () => {
  test("keeps template preview and export controls usable without live resume data", async ({
    page,
    request,
  }) => {
    test.setTimeout(60_000);

    const user = buildTestUser("resume-template-preview");

    await registerTestUser(request, user);

    await page.route("**/api/v1/jobs**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          items: [],
          total: 0,
          page: 1,
          page_size: 100,
          total_pages: 0,
        }),
      });
    });

    await page.route("**/api/v1/resume/versions", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([
          {
            id: "resume-1",
            filename: "resume-2026.pdf",
            created_at: "2026-03-21T12:00:00Z",
            is_default: true,
            parsed_text: "Senior frontend engineer",
          },
        ]),
      });
    });

    await page.route("**/api/v1/resume/templates", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([
          { id: "professional", name: "Professional", description: "Balanced layout." },
          { id: "compact", name: "Compact", description: "Dense one-page layout." },
        ]),
      });
    });

    await page.route("**/api/v1/resume/versions/resume-1/preview?**", async (route) => {
      const url = new URL(route.request().url());
      const templateId = url.searchParams.get("template_id") ?? "professional";
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          template_id: templateId,
          html: `<section>${templateId} preview</section>`,
        }),
      });
    });

    await page.route("**/api/v1/resume/versions/resume-1/export?**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/pdf",
        headers: {
          "content-disposition": 'attachment; filename="resume-2026-compact.pdf"',
        },
        body: "pdf-bytes",
      });
    });

    await loginThroughUi(page, user);

    await page.goto("/resume");
    await expect(
      page.getByRole("main").getByRole("heading", { name: "Resume Builder", exact: true })
    ).toBeVisible();

    await page.getByRole("button", { name: /^versions$/i }).click();
    await expect(page.getByText("resume-2026.pdf", { exact: true })).toBeVisible();
    await page.getByText("resume-2026.pdf", { exact: true }).click();

    await expect(page.getByRole("heading", { name: "resume-2026.pdf", exact: true })).toBeVisible();
    await expect(page.getByLabel("Template")).toHaveValue("professional");
    await expect(page.getByText("professional preview", { exact: true })).toBeVisible();

    await page.getByLabel("Template").selectOption("compact");
    await expect(page.getByText("compact preview", { exact: true })).toBeVisible();
    await expect(page.getByText("Dense one-page layout.", { exact: true })).toBeVisible();

    const exportRequest = page.waitForRequest(
      (candidate) =>
        candidate.url().includes("/api/v1/resume/versions/resume-1/export") &&
        candidate.url().includes("template_id=compact")
    );
    await page.getByRole("button", { name: /^export pdf$/i }).click();
    await exportRequest;
  });
});
