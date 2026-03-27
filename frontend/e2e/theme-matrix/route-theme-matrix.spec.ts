import { expect, test, type Page } from "@playwright/test";

import { buildTestUser, loginThroughUi, registerTestUser } from "../support/auth";
import { THEME_FAMILIES, normalizeThemeSnapshot, seedThemePreference } from "../support/theme";

const MODES = ["light", "dark"] as const;
const REPRESENTATIVE_ROUTES = [
  {
    path: "/",
    locator: (page: Page) =>
      page.getByRole("main").getByRole("heading", { name: "Command Center", exact: true }),
  },
  {
    path: "/targets",
    locator: (page: Page) =>
      page.getByRole("main").getByRole("heading", { name: "Scrape Targets", exact: true }),
  },
  {
    path: "/settings",
    locator: (page: Page) =>
      page.getByText("Appearance", { exact: true }).first(),
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

        await expect.poll(async () => page.evaluate(normalizeThemeSnapshot)).toMatchObject(
          expectedThemeState(family, mode)
        );

        await expect(route.locator(page)).toBeVisible();
        await expect(page.getByRole("button", { name: /logout/i })).toBeVisible();
        await expect(page.getByRole("button", { name: /toggle color mode/i })).toBeVisible();

        if (route.path === "/targets") {
          await expect(page.getByRole("button", { name: /run target batch/i })).toBeVisible();
          await expect(page.getByRole("button", { name: /scraper log/i })).toBeVisible();
        }
      }
    });
  }
}
