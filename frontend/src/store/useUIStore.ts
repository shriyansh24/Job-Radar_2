import { create } from "zustand";

const THEME_STORAGE_KEY = "jobradar.theme";

interface UIState {
  sidebarCollapsed: boolean;
  theme: "dark" | "light";
  toggleSidebar: () => void;
  setTheme: (theme: "dark" | "light") => void;
  toggleTheme: () => void;
}

function applyTheme(theme: "dark" | "light") {
  if (typeof document === "undefined") return;
  document.documentElement.classList.toggle("dark", theme === "dark");
  document.documentElement.style.colorScheme = theme;
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

function getInitialTheme(): "dark" | "light" {
  if (typeof window === "undefined") return "dark";
  const stored = getStorage()?.getItem(THEME_STORAGE_KEY);
  if (stored === "dark" || stored === "light") return stored;
  return window.matchMedia?.("(prefers-color-scheme: dark)")?.matches
    ? "dark"
    : "light";
}

export const useUIStore = create<UIState>((set, get) => {
  const initialTheme = getInitialTheme();
  applyTheme(initialTheme);

  return {
    sidebarCollapsed: false,
    theme: initialTheme,
    toggleSidebar: () =>
      set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
    setTheme: (theme) => {
      applyTheme(theme);
      getStorage()?.setItem(THEME_STORAGE_KEY, theme);
      set({ theme });
    },
    toggleTheme: () => {
      const next = get().theme === "dark" ? "light" : "dark";
      get().setTheme(next);
    },
  };
});
