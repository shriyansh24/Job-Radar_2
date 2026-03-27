import { expect, test } from "@playwright/test";

import { buildTestUser, loginThroughUi, registerTestUser } from "../support/auth";
import { THEME_FAMILIES, normalizeThemeSnapshot, seedThemePreference } from "../support/theme";

test.describe("theme-matrix/theme-persistence", () => {
  test("persists all four theme families through reload", async ({ page, request }) => {
    const user = buildTestUser("theme-matrix");

    await registerTestUser(request, user);
    await loginThroughUi(page, user);

    for (const family of THEME_FAMILIES) {
      await seedThemePreference(page, family, "dark");
      await page.goto("/");
      await expect.poll(async () => page.evaluate(normalizeThemeSnapshot)).toMatchObject(
        family === "default"
          ? {
              themeFamily: null,
              dark: true,
              mode: "dark",
              themeFamilyStored: "default",
            }
          : {
              themeFamily: family,
              dark: true,
              mode: "dark",
              themeFamilyStored: family,
            }
      );

      await page.reload();

      await expect.poll(async () => page.evaluate(normalizeThemeSnapshot)).toMatchObject(
        family === "default"
          ? {
              themeFamily: null,
              dark: true,
              mode: "dark",
              themeFamilyStored: "default",
            }
          : {
              themeFamily: family,
              dark: true,
              mode: "dark",
              themeFamilyStored: family,
            }
      );
    }
  });
});
