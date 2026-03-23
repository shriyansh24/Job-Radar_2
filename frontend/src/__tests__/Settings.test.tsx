import { screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { renderWithProviders } from "./testUtils";

const settingsMocks = vi.hoisted(() => ({
  getSettings: vi.fn(),
  listSearches: vi.fn(),
  updateSettings: vi.fn(),
  createSearch: vi.fn(),
  deleteSearch: vi.fn(),
  exportData: vi.fn(),
  importData: vi.fn(),
  triggerScraper: vi.fn(),
  logout: vi.fn(),
  setTheme: vi.fn(),
}));

vi.mock("../api/settings", () => ({
  settingsApi: {
    getSettings: settingsMocks.getSettings,
    listSearches: settingsMocks.listSearches,
    updateSettings: settingsMocks.updateSettings,
    createSearch: settingsMocks.createSearch,
    deleteSearch: settingsMocks.deleteSearch,
  },
}));

vi.mock("../api/admin", () => ({
  adminApi: {
    exportData: settingsMocks.exportData,
    importData: settingsMocks.importData,
  },
}));

vi.mock("../api/scraper", () => ({
  scraperApi: {
    triggerScraper: settingsMocks.triggerScraper,
  },
}));

vi.mock("../components/scraper/ScraperControlPanel", () => ({
  default: () => <div>Scraper control mock</div>,
}));

vi.mock("../store/useAuthStore", () => ({
  useAuthStore: (
    selector: (state: { logout: () => Promise<void> }) => unknown
  ) => selector({ logout: settingsMocks.logout }),
}));

vi.mock("../store/useUIStore", () => ({
  useUIStore: () => ({
    theme: "dark",
    setTheme: settingsMocks.setTheme,
  }),
}));

import Settings from "../pages/Settings";

describe("Settings page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    settingsMocks.getSettings.mockResolvedValue({
      data: {
        theme: "dark",
        notifications_enabled: true,
        auto_apply_enabled: false,
      },
    });
    settingsMocks.listSearches.mockResolvedValue({
      data: [
        {
          id: "search-1",
          name: "Remote React",
          filters: { q: "react", remote_type: "remote" },
          alert_enabled: true,
        },
      ],
    });
    settingsMocks.updateSettings.mockResolvedValue({ data: null });
    settingsMocks.createSearch.mockResolvedValue({ data: null });
    settingsMocks.deleteSearch.mockResolvedValue({ data: null });
    settingsMocks.triggerScraper.mockResolvedValue({ data: null });
    settingsMocks.logout.mockResolvedValue(undefined);
  });

  it("renders settings sections, saved search data, and scraper controls", async () => {
    renderWithProviders(<Settings />);

    expect(await screen.findByText("App Settings")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Settings" })).toBeInTheDocument();
    expect(screen.getByText("API Keys")).toBeInTheDocument();
    expect(screen.getByText("Saved Searches")).toBeInTheDocument();
    expect(screen.getByText("Remote React")).toBeInTheDocument();
    expect(screen.getByText("q: react")).toBeInTheDocument();
    expect(screen.getByText("Scraper control mock")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Run All Scrapers/i })).toBeInTheDocument();
  });
});
