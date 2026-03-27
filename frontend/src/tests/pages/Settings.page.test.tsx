import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { renderWithProviders } from "../support/test-utils";

const settingsMocks = vi.hoisted(() => ({
  getSettings: vi.fn(),
  listSearches: vi.fn(),
  listIntegrations: vi.fn(),
  updateSettings: vi.fn(),
  updateSearch: vi.fn(),
  createSearch: vi.fn(),
  deleteSearch: vi.fn(),
  upsertIntegration: vi.fn(),
  deleteIntegration: vi.fn(),
  exportData: vi.fn(),
  clearData: vi.fn(),
  changePassword: vi.fn(),
  deleteAccount: vi.fn(),
}));

vi.mock("../../api/settings", () => ({
  settingsApi: {
    getSettings: settingsMocks.getSettings,
    listSearches: settingsMocks.listSearches,
    listIntegrations: settingsMocks.listIntegrations,
    updateSettings: settingsMocks.updateSettings,
    updateSearch: settingsMocks.updateSearch,
    createSearch: settingsMocks.createSearch,
    deleteSearch: settingsMocks.deleteSearch,
    upsertIntegration: settingsMocks.upsertIntegration,
    deleteIntegration: settingsMocks.deleteIntegration,
  },
}));

vi.mock("../../api/admin", () => ({
  adminApi: {
    exportData: settingsMocks.exportData,
    clearData: settingsMocks.clearData,
  },
}));

vi.mock("../../api/auth", () => ({
  changePasswordApi: settingsMocks.changePassword,
  deleteAccountApi: settingsMocks.deleteAccount,
}));

vi.mock("../../store/useAuthStore", () => ({
  useAuthStore: (selector: (state: { user: { email: string } | null }) => unknown) =>
    selector({ user: { email: "owner@jobradar.dev" } }),
}));

import Settings from "../../pages/Settings";

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
          last_checked_at: "2026-03-22T10:00:00Z",
        },
      ],
    });
    settingsMocks.listIntegrations.mockResolvedValue({
      data: [
        {
          provider: "openrouter",
          connected: true,
          status: "connected",
          masked_value: "sk-or-v1-****",
          updated_at: "2026-03-22T09:00:00Z",
        },
        {
          provider: "serpapi",
          connected: false,
          status: "missing",
          masked_value: null,
          updated_at: null,
        },
      ],
    });
    settingsMocks.updateSettings.mockResolvedValue({ data: null });
    settingsMocks.updateSearch.mockResolvedValue({ data: null });
    settingsMocks.createSearch.mockResolvedValue({ data: null });
    settingsMocks.deleteSearch.mockResolvedValue({ data: null });
    settingsMocks.upsertIntegration.mockResolvedValue({ data: null });
    settingsMocks.deleteIntegration.mockResolvedValue({ data: null });
    settingsMocks.exportData.mockResolvedValue({ data: new Blob(["{}"], { type: "application/json" }) });
    settingsMocks.clearData.mockResolvedValue({ data: { rows_deleted: 0 } });
    settingsMocks.changePassword.mockResolvedValue({ data: null });
    settingsMocks.deleteAccount.mockResolvedValue({ data: null });
  });

  it("renders the redesigned settings workspace with saved searches and integrations", async () => {
    const user = userEvent.setup();
    renderWithProviders(<Settings />);

    expect(await screen.findByRole("heading", { name: "Settings" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /save changes/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^workspace$/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^security$/i })).toBeInTheDocument();
    expect(screen.getAllByText("owner@jobradar.dev").length).toBeGreaterThan(0);

    await user.click(screen.getByRole("button", { name: /^searches$/i }));
    expect(await screen.findByText("Remote React")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /new search/i })).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /^integrations$/i }));
    expect(await screen.findByText("OpenRouter")).toBeInTheDocument();
    expect(screen.getByText(/sk-or-v1/i)).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /^data$/i }));
    expect(await screen.findByRole("button", { name: /export data/i })).toBeInTheDocument();
  });
});
