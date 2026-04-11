import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useUIStore, parseThemePreference, serializeThemePreference } from "../../store/useUIStore";

function resetStore() {
  useUIStore.setState({
    sidebarCollapsed: false,
    mobileNavOpen: false,
    mode: "light",
    theme: "light",
    themeFamily: "default",
  });
}

function mockMatchMedia(matchesDark: boolean) {
  const originalMatchMedia = window.matchMedia;
  window.matchMedia = vi.fn().mockImplementation((query: string) => ({
    matches: query === "(prefers-color-scheme: dark)" ? matchesDark : false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  }));
  return () => {
    window.matchMedia = originalMatchMedia;
  };
}

beforeEach(() => {
  localStorage.clear();
  resetStore();
  // Reset DOM class and attributes
  document.documentElement.classList.remove("dark");
  document.documentElement.removeAttribute("data-theme");
});

afterEach(() => {
  vi.restoreAllMocks();
});

// ---------------------------------------------------------------------------
// parseThemePreference / serializeThemePreference (pure functions)
// ---------------------------------------------------------------------------

describe("serializeThemePreference", () => {
  it("serializes default family as just the mode", () => {
    expect(serializeThemePreference("default", "dark")).toBe("dark");
    expect(serializeThemePreference("default", "light")).toBe("light");
  });

  it("serializes non-default family as family:mode", () => {
    expect(serializeThemePreference("terminal", "dark")).toBe("terminal:dark");
    expect(serializeThemePreference("blueprint", "light")).toBe("blueprint:light");
  });
});

describe("parseThemePreference", () => {
  it("parses plain mode strings", () => {
    expect(parseThemePreference("dark")).toEqual({ mode: "dark", themeFamily: "default" });
    expect(parseThemePreference("light")).toEqual({ mode: "light", themeFamily: "default" });
  });

  it("parses family:mode format", () => {
    expect(parseThemePreference("terminal:dark")).toEqual({ mode: "dark", themeFamily: "terminal" });
    expect(parseThemePreference("blueprint:light")).toEqual({ mode: "light", themeFamily: "blueprint" });
  });

  it("falls back to defaults for unrecognised values", () => {
    const restore = mockMatchMedia(true);
    expect(parseThemePreference("nonsense")).toEqual({ mode: "dark", themeFamily: "default" });
    restore();
  });

  it("falls back to defaults for null / undefined", () => {
    const restore = mockMatchMedia(false);
    expect(parseThemePreference(null)).toEqual({ mode: "light", themeFamily: "default" });
    expect(parseThemePreference(undefined)).toEqual({ mode: "light", themeFamily: "default" });
    expect(parseThemePreference("system")).toEqual({ mode: "light", themeFamily: "default" });
    restore();
  });

  it("falls back to system dark mode when stored family or mode is invalid", () => {
    const restore = mockMatchMedia(true);
    expect(parseThemePreference("invalid:dark")).toEqual({ mode: "dark", themeFamily: "default" });
    expect(parseThemePreference("terminal:invalid")).toEqual({
      mode: "dark",
      themeFamily: "default",
    });
    restore();
  });
});

// ---------------------------------------------------------------------------
// Sidebar
// ---------------------------------------------------------------------------

describe("useUIStore – toggleSidebar", () => {
  it("flips sidebarCollapsed from false to true", () => {
    useUIStore.getState().toggleSidebar();
    expect(useUIStore.getState().sidebarCollapsed).toBe(true);
  });

  it("flips sidebarCollapsed back to false on second call", () => {
    useUIStore.getState().toggleSidebar();
    useUIStore.getState().toggleSidebar();
    expect(useUIStore.getState().sidebarCollapsed).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// Mobile nav
// ---------------------------------------------------------------------------

describe("useUIStore – mobile nav", () => {
  it("setMobileNavOpen sets value", () => {
    useUIStore.getState().setMobileNavOpen(true);
    expect(useUIStore.getState().mobileNavOpen).toBe(true);

    useUIStore.getState().setMobileNavOpen(false);
    expect(useUIStore.getState().mobileNavOpen).toBe(false);
  });

  it("toggleMobileNav flips state", () => {
    useUIStore.getState().toggleMobileNav();
    expect(useUIStore.getState().mobileNavOpen).toBe(true);

    useUIStore.getState().toggleMobileNav();
    expect(useUIStore.getState().mobileNavOpen).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// Mode / theme
// ---------------------------------------------------------------------------

describe("useUIStore – toggleMode", () => {
  it("switches from light to dark", () => {
    useUIStore.setState({ mode: "light", theme: "light" });
    useUIStore.getState().toggleMode();
    expect(useUIStore.getState().mode).toBe("dark");
  });

  it("switches from dark to light", () => {
    useUIStore.setState({ mode: "dark", theme: "dark" });
    useUIStore.getState().toggleMode();
    expect(useUIStore.getState().mode).toBe("light");
  });

  it("applies dark class to document.documentElement when mode is dark", () => {
    useUIStore.setState({ mode: "light", theme: "light" });
    useUIStore.getState().setMode("dark");
    expect(document.documentElement.classList.contains("dark")).toBe(true);
  });

  it("removes dark class when mode is light", () => {
    useUIStore.setState({ mode: "dark", theme: "dark" });
    document.documentElement.classList.add("dark");
    useUIStore.getState().setMode("light");
    expect(document.documentElement.classList.contains("dark")).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// Theme family
// ---------------------------------------------------------------------------

describe("useUIStore – setThemeFamily", () => {
  it("sets theme family in store state", () => {
    useUIStore.getState().setThemeFamily("terminal");
    expect(useUIStore.getState().themeFamily).toBe("terminal");
  });

  it("sets data-theme attribute on documentElement", () => {
    useUIStore.getState().setThemeFamily("blueprint");
    expect(document.documentElement.getAttribute("data-theme")).toBe("blueprint");
  });

  it("removes data-theme attribute for default family", () => {
    document.documentElement.setAttribute("data-theme", "terminal");
    useUIStore.getState().setThemeFamily("default");
    expect(document.documentElement.getAttribute("data-theme")).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// setThemePreference (atomic)
// ---------------------------------------------------------------------------

describe("useUIStore – setThemePreference", () => {
  it("sets both themeFamily and mode atomically", () => {
    useUIStore.getState().setThemePreference("phosphor", "dark");
    const state = useUIStore.getState();
    expect(state.themeFamily).toBe("phosphor");
    expect(state.mode).toBe("dark");
  });
});

// ---------------------------------------------------------------------------
// localStorage persistence
// ---------------------------------------------------------------------------

describe("useUIStore – localStorage persistence", () => {
  it("persists mode to localStorage", () => {
    useUIStore.getState().setMode("dark");
    expect(localStorage.getItem("jobradar.mode")).toBe("dark");
  });

  it("persists themeFamily to localStorage", () => {
    useUIStore.getState().setThemeFamily("terminal");
    expect(localStorage.getItem("jobradar.themeFamily")).toBe("terminal");
  });
});
