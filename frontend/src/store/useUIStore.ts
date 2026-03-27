import { create } from "zustand";

const LEGACY_THEME_STORAGE_KEY = "jobradar.theme";
const MODE_STORAGE_KEYS = ["jobradar.mode", "jobradar-mode", LEGACY_THEME_STORAGE_KEY] as const;
const THEME_FAMILY_STORAGE_KEYS = ["jobradar.themeFamily", "jobradar-theme"] as const;

export type ThemeMode = "dark" | "light";
export type ThemeFamily = "default" | "terminal" | "blueprint" | "phosphor";

const THEME_FAMILIES: ThemeFamily[] = [
  "default",
  "terminal",
  "blueprint",
  "phosphor",
];

interface UIState {
  sidebarCollapsed: boolean;
  mobileNavOpen: boolean;
  theme: ThemeMode;
  mode: ThemeMode;
  themeFamily: ThemeFamily;
  toggleSidebar: () => void;
  setMobileNavOpen: (open: boolean) => void;
  toggleMobileNav: () => void;
  setTheme: (theme: ThemeMode) => void;
  toggleTheme: () => void;
  setMode: (mode: ThemeMode) => void;
  toggleMode: () => void;
  setThemeFamily: (themeFamily: ThemeFamily) => void;
  setThemePreference: (themeFamily: ThemeFamily, mode: ThemeMode) => void;
}

type ThemePreference = {
  mode: ThemeMode;
  themeFamily: ThemeFamily;
};

function isThemeMode(value: string | null | undefined): value is ThemeMode {
  return value === "dark" || value === "light";
}

function isThemeFamily(value: string | null | undefined): value is ThemeFamily {
  return !!value && THEME_FAMILIES.includes(value as ThemeFamily);
}

function getPreferredMode(): ThemeMode {
  if (typeof window === "undefined") return "dark";
  return window.matchMedia?.("(prefers-color-scheme: dark)")?.matches
    ? "dark"
    : "light";
}

export function serializeThemePreference(
  themeFamily: ThemeFamily,
  mode: ThemeMode
): string {
  return themeFamily === "default" ? mode : `${themeFamily}:${mode}`;
}

export function parseThemePreference(value: string | null | undefined): ThemePreference {
  if (!value || value === "system") {
    return { mode: getPreferredMode(), themeFamily: "default" };
  }

  if (isThemeMode(value)) {
    return { mode: value, themeFamily: "default" };
  }

  const [maybeFamily, maybeMode] = value.split(":");
  if (isThemeFamily(maybeFamily) && isThemeMode(maybeMode)) {
    return { mode: maybeMode, themeFamily: maybeFamily };
  }

  return { mode: getPreferredMode(), themeFamily: "default" };
}

function applyTheme(mode: ThemeMode, themeFamily: ThemeFamily) {
  if (typeof document === "undefined") return;
  const root = document.documentElement;
  root.classList.toggle("dark", mode === "dark");
  root.style.colorScheme = mode;

  if (themeFamily === "default") {
    root.removeAttribute("data-theme");
  } else {
    root.setAttribute("data-theme", themeFamily);
  }
}

function getStorage(): Storage | null {
  if (typeof window === "undefined") return null;
  const s = window.localStorage;
  if (!s) return null;
  if (typeof s.getItem !== "function") return null;
  if (typeof s.setItem !== "function") return null;
  if (typeof s.removeItem !== "function") return null;
  return s;
}

function readFirstStorageValue(keys: readonly string[]): string | null {
  const storage = getStorage();
  if (!storage) return null;

  for (const key of keys) {
    const value = storage.getItem(key);
    if (value) return value;
  }

  return null;
}

function persistMode(mode: ThemeMode) {
  const storage = getStorage();
  if (!storage) return;

  storage.setItem("jobradar.mode", mode);
  storage.setItem("jobradar-mode", mode);
  storage.setItem(LEGACY_THEME_STORAGE_KEY, mode);
}

function persistThemeFamily(themeFamily: ThemeFamily) {
  const storage = getStorage();
  if (!storage) return;

  storage.setItem("jobradar.themeFamily", themeFamily);
  storage.setItem("jobradar-theme", themeFamily);
}

function getInitialThemePreference(): ThemePreference {
  if (typeof window === "undefined") {
    return { mode: "dark", themeFamily: "default" };
  }

  const storedMode = readFirstStorageValue(MODE_STORAGE_KEYS);
  const storedThemeFamily = readFirstStorageValue(THEME_FAMILY_STORAGE_KEYS);

  if (isThemeMode(storedMode) && isThemeFamily(storedThemeFamily)) {
    return { mode: storedMode, themeFamily: storedThemeFamily };
  }

  if (isThemeMode(storedMode)) {
    return { mode: storedMode, themeFamily: "default" };
  }

  if (isThemeFamily(storedThemeFamily)) {
    return { mode: getPreferredMode(), themeFamily: storedThemeFamily };
  }

  return parseThemePreference(storedMode);
}

export const useUIStore = create<UIState>((set, get) => {
  const initialThemePreference = getInitialThemePreference();
  applyTheme(initialThemePreference.mode, initialThemePreference.themeFamily);

  function commitThemePreference(themeFamily: ThemeFamily, mode: ThemeMode) {
    applyTheme(mode, themeFamily);
    persistMode(mode);
    persistThemeFamily(themeFamily);
    set({ mode, theme: mode, themeFamily });
  }

  return {
    sidebarCollapsed: false,
    mobileNavOpen: false,
    mode: initialThemePreference.mode,
    theme: initialThemePreference.mode,
    themeFamily: initialThemePreference.themeFamily,
    toggleSidebar: () =>
      set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
    setMobileNavOpen: (mobileNavOpen) => set({ mobileNavOpen }),
    toggleMobileNav: () =>
      set((state) => ({ mobileNavOpen: !state.mobileNavOpen })),
    setTheme: (theme) => {
      commitThemePreference(get().themeFamily, theme);
    },
    toggleTheme: () => {
      const next = get().theme === "dark" ? "light" : "dark";
      get().setTheme(next);
    },
    setMode: (mode) => {
      commitThemePreference(get().themeFamily, mode);
    },
    toggleMode: () => {
      const next = get().mode === "dark" ? "light" : "dark";
      get().setMode(next);
    },
    setThemeFamily: (themeFamily) => {
      commitThemePreference(themeFamily, get().mode);
    },
    setThemePreference: (themeFamily, mode) => {
      commitThemePreference(themeFamily, mode);
    },
  };
});
