import { expect, test, type Page } from "@playwright/test";

import { buildTestUser, loginThroughUi, registerTestUser } from "../support/auth";
import { THEME_FAMILIES, normalizeThemeSnapshot, seedThemePreference } from "../support/theme";

const MODES = ["light", "dark"] as const;
const ROUTE_FAMILY_MATRIX = [
  {
    path: "/",
    locator: (page: Page) =>
      page.getByRole("button", { name: /^browse jobs$/i }),
    assertion: async (page: Page) => {
      await expect(page.getByRole("button", { name: /^browse jobs$/i })).toBeVisible();
      await expect(page.getByRole("button", { name: /^add application$/i })).toBeVisible();
    },
  },
  {
    path: "/resume",
    locator: (page: Page) =>
      page.getByRole("button", { name: /^upload$/i }),
    assertion: async (page: Page) => {
      await expect(page.getByRole("button", { name: /^upload$/i })).toBeVisible();
      await expect(page.getByRole("button", { name: /^versions$/i })).toBeVisible();
      await expect(page.getByRole("button", { name: /^tailor$/i })).toBeVisible();
      await expect(page.getByRole("button", { name: /^council$/i })).toBeVisible();
    },
  },
  {
    path: "/analytics",
    locator: (page: Page) =>
      page.getByText("30 day window", { exact: true }),
    assertion: async (page: Page) => {
      await expect(page.getByText("30 day window", { exact: true })).toBeVisible();
      await expect(page.getByText("Application patterns", { exact: true })).toBeVisible();
    },
  },
  {
    path: "/search-expansion",
    locator: (page: Page) =>
      page.getByRole("button", { name: /^expand query$/i }).first(),
    assertion: async (page: Page) => {
      await expect(page.getByPlaceholder("senior frontend engineer")).toBeVisible();
      await expect(page.getByRole("button", { name: /^expand query$/i }).first()).toBeVisible();
    },
  },
  {
    path: "/settings",
    locator: (page: Page) =>
      page.getByRole("button", { name: /^appearance$/i }),
    assertion: async (page: Page) => {
      await expect(page.getByRole("button", { name: /^appearance$/i })).toBeVisible();
      await expect(page.getByRole("button", { name: /^integrations$/i })).toBeVisible();
    },
  },
  {
    path: "/networking",
    locator: (page: Page) => page.getByRole("button", { name: /^new contact$/i }),
    assertion: async (page: Page) => {
      await expect(page.getByRole("button", { name: /^new contact$/i })).toBeVisible();
      await expect(page.getByText("Contacts", { exact: true }).first()).toBeVisible();
    },
  },
  {
    path: "/email",
    locator: (page: Page) => page.getByText("Signal log", { exact: true }),
    assertion: async (page: Page) => {
      await expect(page.getByText("Signal log", { exact: true })).toBeVisible();
      await expect(page.getByRole("button", { name: /^process signal$/i })).toBeVisible();
    },
  },
  {
    path: "/onboarding",
    locator: (page: Page) => page.getByRole("button", { name: /^next$/i }),
    assertion: async (page: Page) => {
      await expect(page.getByRole("heading", { name: "Onboarding", exact: true })).toBeVisible();
      await expect(page.getByRole("button", { name: /^next$/i })).toBeVisible();
    },
  },
  {
    path: "/outcomes",
    locator: (page: Page) => page.getByText("Response Rate", { exact: true }),
    assertion: async (page: Page) => {
      await expect(page.getByText("Response Rate", { exact: true })).toBeVisible();
      await expect(page.getByText("Keep it honest", { exact: true })).toBeVisible();
    },
  },
  {
    path: "/copilot",
    locator: (page: Page) => page.getByText("Switch tasks", { exact: true }),
    assertion: async (page: Page) => {
      await expect(page.getByText("Switch tasks", { exact: true })).toBeVisible();
      await expect(page.getByRole("button", { name: /^assistant$/i })).toBeVisible();
    },
  },
  {
    path: "/canonical-jobs",
    locator: (page: Page) => page.getByRole("button", { name: /show stale/i }),
    assertion: async (page: Page) => {
      await expect(page.getByRole("heading", { name: "Canonical Jobs", exact: true })).toBeVisible();
      await expect(page.getByRole("button", { name: /show stale/i })).toBeVisible();
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

test("theme-matrix/route-theme-matrix keeps route families stable across all 8 theme combinations", async ({
  page,
  request,
}) => {
  test.setTimeout(480_000);

  const user = buildTestUser("route-theme-matrix");

  await registerTestUser(request, user);
  await loginThroughUi(page, user);
  await expect(page.getByRole("button", { name: /logout/i })).toBeVisible();

  for (const family of THEME_FAMILIES) {
    for (const mode of MODES) {
      for (const route of ROUTE_FAMILY_MATRIX) {
        await seedThemePreference(page, family, mode);
        await page.goto(route.path, { waitUntil: "domcontentloaded" });

        await expect.poll(async () => page.evaluate(normalizeThemeSnapshot)).toMatchObject(
          expectedThemeState(family, mode)
        );

        await expect(route.locator(page)).toBeVisible();
        await route.assertion(page);
      }
    }
  }
});
