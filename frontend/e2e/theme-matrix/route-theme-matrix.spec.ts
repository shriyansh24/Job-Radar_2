import { expect, test, type Page } from "@playwright/test";

import { buildTestUser, registerTestUser } from "../support/auth";
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
      page.getByRole("button", { name: /^exact$/i }),
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
      page.getByRole("button", { name: /^upload$/i }),
    assertion: async (page: Page) => {
      await expect(page.getByRole("button", { name: /^upload$/i })).toBeVisible();
      await expect(page.getByText(/drag and drop a resume/i)).toBeVisible();
    },
  },
  {
    path: "/interview",
    locator: (page: Page) =>
      page.getByRole("button", { name: /^practice$/i }),
    assertion: async (page: Page) => {
      await expect(page.getByRole("button", { name: /^practice$/i })).toBeVisible();
      await expect(page.getByRole("button", { name: /^prepare$/i })).toBeVisible();
      await expect(page.getByRole("button", { name: /^history$/i })).toBeVisible();
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
] as const;

async function loginWithStableSubmit(
  page: Page,
  user: { email: string; password: string }
) {
  const response = await page.request.post("/api/v1/auth/login", {
    data: {
      email: user.email,
      password: user.password,
    },
  });

  expect(response.ok(), `login status ${response.status()}`).toBeTruthy();
  await page.goto("/");
  await expect(page).toHaveURL(/\/$/);
}

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
      await loginWithStableSubmit(page, user);

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
