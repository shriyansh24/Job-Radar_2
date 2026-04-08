import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import {
  serializeThemePreference,
  parseThemePreference,
} from "@/store/useUIStore";

describe("Theme Preference Utilities", () => {
  describe("serializeThemePreference", () => {
    it("should return just the mode if themeFamily is 'default'", () => {
      expect(serializeThemePreference("default", "dark")).toBe("dark");
      expect(serializeThemePreference("default", "light")).toBe("light");
    });

    it("should return 'themeFamily:mode' if themeFamily is not 'default'", () => {
      expect(serializeThemePreference("terminal", "dark")).toBe("terminal:dark");
      expect(serializeThemePreference("blueprint", "light")).toBe("blueprint:light");
      expect(serializeThemePreference("phosphor", "dark")).toBe("phosphor:dark");
    });
  });

  describe("parseThemePreference", () => {
    let originalMatchMedia: typeof window.matchMedia;

    beforeEach(() => {
      originalMatchMedia = window.matchMedia;
    });

    afterEach(() => {
      window.matchMedia = originalMatchMedia;
    });

    const mockMatchMedia = (matchesDark: boolean) => {
      window.matchMedia = vi.fn().mockImplementation((query) => ({
        matches: query === "(prefers-color-scheme: dark)" ? matchesDark : false,
        media: query,
        onchange: null,
        addListener: vi.fn(), // deprecated
        removeListener: vi.fn(), // deprecated
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      }));
    };

    it("should default to system preference ('dark') and 'default' theme family when value is falsy or 'system'", () => {
      mockMatchMedia(true);
      expect(parseThemePreference(null)).toEqual({ mode: "dark", themeFamily: "default" });
      expect(parseThemePreference(undefined)).toEqual({ mode: "dark", themeFamily: "default" });
      expect(parseThemePreference("")).toEqual({ mode: "dark", themeFamily: "default" });
      expect(parseThemePreference("system")).toEqual({ mode: "dark", themeFamily: "default" });
    });

    it("should default to system preference ('light') and 'default' theme family when value is falsy or 'system'", () => {
      mockMatchMedia(false);
      expect(parseThemePreference(null)).toEqual({ mode: "light", themeFamily: "default" });
      expect(parseThemePreference("system")).toEqual({ mode: "light", themeFamily: "default" });
    });

    it("should parse pure mode strings correctly", () => {
      expect(parseThemePreference("dark")).toEqual({ mode: "dark", themeFamily: "default" });
      expect(parseThemePreference("light")).toEqual({ mode: "light", themeFamily: "default" });
    });

    it("should parse compound strings correctly", () => {
      expect(parseThemePreference("terminal:dark")).toEqual({ mode: "dark", themeFamily: "terminal" });
      expect(parseThemePreference("blueprint:light")).toEqual({ mode: "light", themeFamily: "blueprint" });
    });

    it("should fallback to system preference if themeFamily is invalid", () => {
      mockMatchMedia(true);
      expect(parseThemePreference("invalid:dark")).toEqual({ mode: "dark", themeFamily: "default" });
    });

    it("should fallback to system preference if mode is invalid", () => {
      mockMatchMedia(false);
      expect(parseThemePreference("terminal:invalid")).toEqual({ mode: "light", themeFamily: "default" });
    });

    it("should fallback to system preference for completely unparseable values", () => {
      mockMatchMedia(true);
      expect(parseThemePreference("random-garbage")).toEqual({ mode: "dark", themeFamily: "default" });
    });
  });
});
