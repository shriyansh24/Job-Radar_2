import type { Page } from "@playwright/test";

export const THEME_FAMILIES = ["default", "terminal", "blueprint", "phosphor"] as const;

export async function seedThemePreference(
  page: Page,
  family: (typeof THEME_FAMILIES)[number],
  mode: "light" | "dark"
): Promise<void> {
  await page.evaluate(
    ({ family: nextFamily, nextMode }) => {
      localStorage.setItem("jobradar.themeFamily", nextFamily);
      localStorage.setItem("jobradar-theme", nextFamily);
      localStorage.setItem("jobradar.mode", nextMode);
      localStorage.setItem("jobradar-mode", nextMode);
      localStorage.setItem("jobradar.theme", nextMode);
    },
    { family, nextMode: mode }
  );
}

export function normalizeThemeSnapshot() {
  return {
    themeFamily: document.documentElement.getAttribute("data-theme"),
    dark: document.documentElement.classList.contains("dark"),
    mode: localStorage.getItem("jobradar.mode"),
    legacyMode: localStorage.getItem("jobradar.theme"),
    themeFamilyStored: localStorage.getItem("jobradar.themeFamily"),
  };
}
