import { expect, test, type Page } from "@playwright/test";

import { buildTestUser, loginThroughUi, registerTestUser } from "../support/auth";
import { THEME_FAMILIES, normalizeThemeSnapshot, seedThemePreference } from "../support/theme";

const MODES = ["light", "dark"] as const;
const REPRESENTATIVE_ROUTES = [
  {
    path: "/",
    locator: (page: Page) =>
      page.getByRole("main").getByRole("heading", { name: "Command Center", exact: true }),
    assertion: async (page: Page) => {
      await expect(page.getByRole("button", { name: /^browse jobs$/i })).toBeVisible();
      await expect(page.getByRole("button", { name: /^add application$/i })).toBeVisible();
    },
  },
  {
    path: "/jobs",
    locator: (page: Page) =>
      page.getByRole("main").getByRole("heading", { name: "Jobs", exact: true }),
    assertion: async (page: Page) => {
      await expect(page.getByRole("button", { name: /^exact$/i })).toBeVisible();
      await expect(page.getByRole("button", { name: /^semantic$/i })).toBeVisible();
      await expect(page.getByPlaceholder("Search jobs")).toBeVisible();
    },
  },
  {
    path: "/pipeline",
    locator: (page: Page) =>
      page.getByRole("button", { name: /^auto-apply$/i }),
    assertion: async (page: Page) => {
      await expect(page.getByRole("button", { name: /^auto-apply$/i })).toBeVisible();
      await expect(page.getByRole("heading", { name: "Stages", exact: true })).toBeVisible();
    },
  },
  {
    path: "/resume",
    locator: (page: Page) =>
      page.getByRole("main").getByRole("heading", { name: "Resume Builder", exact: true }),
    assertion: async (page: Page) => {
      await expect(page.getByRole("button", { name: /^upload$/i })).toBeVisible();
      await expect(page.getByText(/drag and drop a resume/i)).toBeVisible();
    },
  },
  {
    path: "/analytics",
    locator: (page: Page) =>
      page.getByRole("button", { name: /last 30 days/i }),
    assertion: async (page: Page) => {
      await expect(page.getByRole("button", { name: /last 30 days/i })).toBeVisible();
      await expect(page.getByRole("button", { name: /export pdf/i })).toBeVisible();
    },
  },
  {
    path: "/settings",
    locator: (page: Page) =>
      page.getByRole("main").getByRole("heading", { name: "Settings", exact: true }),
    assertion: async (page: Page) => {
      await expect(page.getByRole("button", { name: /^appearance$/i })).toBeVisible();
      await expect(page.getByRole("button", { name: /^integrations$/i })).toBeVisible();
    },
  },
] as const;

function expectedThemeState(
  family: (typeof THEME_FAMILIES)[number],
  mode: (typeof MODES)[number]
) {
  return family === "default"
    ? {
        themeFamily: null,
        dark: mode === "dark",
        mode,
        themeFamilyStored: "default",
      }
    : {
        themeFamily: family,
        dark: mode === "dark",
        mode,
        themeFamilyStored: family,
      };
}

test.describe.configure({ mode: "serial" });

for (const family of THEME_FAMILIES) {
  for (const mode of MODES) {
    test(`theme-matrix/route-theme-matrix: ${family} ${mode} keeps representative routes stable`, async ({
      page,
      request,
    }) => {
      test.setTimeout(90_000);

      const user = buildTestUser(`route-theme-${family}-${mode}`);

      await registerTestUser(request, user);
      await loginThroughUi(page, user);

      for (const route of REPRESENTATIVE_ROUTES) {
        await seedThemePreference(page, family, mode);
        await page.goto(route.path);
        await page.reload();

        await expect.poll(async () => page.evaluate(normalizeThemeSnapshot)).toMatchObject(
          expectedThemeState(family, mode)
        );

        await expect(route.locator(page)).toBeVisible();
        await expect(page.getByRole("button", { name: /logout/i })).toBeVisible();
        await expect(page.getByRole("button", { name: /toggle color mode/i })).toBeVisible();
        await route.assertion(page);
      }
    });
  }
}
