import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { renderWithProviders } from "../support/renderWithProviders";

const settingsMocks = vi.hoisted(() => ({
  getSettings: vi.fn(),
  listSearches: vi.fn(),
  listIntegrations: vi.fn(),
  updateSettings: vi.fn(),
  updateSearch: vi.fn(),
  checkSearch: vi.fn(),
  createSearch: vi.fn(),
  deleteSearch: vi.fn(),
  upsertIntegration: vi.fn(),
  deleteIntegration: vi.fn(),
  buildGoogleConnectUrl: vi.fn(),
  syncGoogleIntegration: vi.fn(),
  exportData: vi.fn(),
  clearData: vi.fn(),
  changePassword: vi.fn(),
  deleteAccount: vi.fn(),
}));

const toastMock = vi.hoisted(() => vi.fn());

vi.mock("../../api/settings", () => ({
  settingsApi: {
    getSettings: settingsMocks.getSettings,
    listSearches: settingsMocks.listSearches,
    listIntegrations: settingsMocks.listIntegrations,
    updateSettings: settingsMocks.updateSettings,
    updateSearch: settingsMocks.updateSearch,
    checkSearch: settingsMocks.checkSearch,
    createSearch: settingsMocks.createSearch,
    deleteSearch: settingsMocks.deleteSearch,
    upsertIntegration: settingsMocks.upsertIntegration,
    deleteIntegration: settingsMocks.deleteIntegration,
    buildGoogleConnectUrl: settingsMocks.buildGoogleConnectUrl,
    syncGoogleIntegration: settingsMocks.syncGoogleIntegration,
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

vi.mock("../../components/ui/toastService", () => ({
  toast: toastMock,
}));

vi.mock("../../store/useAuthStore", () => ({
  useAuthStore: (selector: (state: { user: { email: string } | null }) => unknown) =>
    selector({ user: { email: "owner@jobradar.dev" } }),
}));

import Settings from "../../pages/Settings";

describe("Settings page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.history.replaceState({}, "", "/settings");
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
          last_matched_at: "2026-03-22T10:05:00Z",
          last_match_count: 3,
          last_error: null,
          created_at: "2026-03-20T10:00:00Z",
        },
      ],
    });
    settingsMocks.listIntegrations.mockResolvedValue({
      data: [
        {
          provider: "openrouter",
          auth_type: "api_key",
          connected: true,
          status: "connected",
          masked_value: "sk-or-v1-****",
          account_email: null,
          scopes: [],
          updated_at: "2026-03-22T09:00:00Z",
          last_validated_at: null,
          last_synced_at: null,
          last_error: null,
        },
        {
          provider: "serpapi",
          auth_type: "api_key",
          connected: false,
          status: "not_configured",
          masked_value: null,
          account_email: null,
          scopes: [],
          updated_at: null,
          last_validated_at: null,
          last_synced_at: null,
          last_error: null,
        },
        {
          provider: "google",
          auth_type: "oauth",
          connected: true,
          status: "connected",
          masked_value: null,
          account_email: "owner@jobradar.dev",
          scopes: ["https://www.googleapis.com/auth/gmail.readonly"],
          updated_at: "2026-03-22T09:10:00Z",
          last_validated_at: "2026-03-22T09:10:00Z",
          last_synced_at: "2026-03-22T09:20:00Z",
          last_error: null,
        },
      ],
    });
    settingsMocks.updateSettings.mockResolvedValue({ data: null });
    settingsMocks.updateSearch.mockResolvedValue({ data: null });
    settingsMocks.checkSearch.mockResolvedValue({
      data: {
        status: "matched",
        new_matches: 1,
        notification_created: true,
        notification_id: "notif-1",
        link: "/jobs?q=react",
        search: {
          id: "search-1",
          name: "Remote React",
          filters: { q: "react", remote_type: "remote" },
          alert_enabled: true,
          last_checked_at: "2026-03-22T10:10:00Z",
          last_matched_at: "2026-03-22T10:10:00Z",
          last_match_count: 1,
          last_error: null,
          created_at: "2026-03-20T10:00:00Z",
        },
      },
    });
    settingsMocks.createSearch.mockResolvedValue({ data: null });
    settingsMocks.deleteSearch.mockResolvedValue({ data: null });
    settingsMocks.upsertIntegration.mockResolvedValue({ data: null });
    settingsMocks.deleteIntegration.mockResolvedValue({ data: null });
    settingsMocks.buildGoogleConnectUrl.mockReturnValue("http://localhost:8000/api/v1/settings/integrations/google/connect");
    settingsMocks.syncGoogleIntegration.mockResolvedValue({
      data: {
        provider: "google",
        messages_seen: 3,
        messages_processed: 2,
        messages_failed: 0,
        duplicates_skipped: 1,
        signals_detected: 2,
        transitions_applied: 1,
        last_synced_at: "2026-03-22T09:20:00Z",
      },
    });
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
    expect(screen.getByText(/Last match 3 jobs/i)).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /^integrations$/i }));
    expect(await screen.findByText("OpenRouter")).toBeInTheDocument();
    expect(screen.getByText(/sk-or-v1/i)).toBeInTheDocument();
    expect(screen.getByText("Google Gmail")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /sync gmail/i })).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /^data$/i }));
    expect(await screen.findByRole("button", { name: /export data/i })).toBeInTheDocument();
  });

  it("runs a saved search check from the settings surface", async () => {
    const user = userEvent.setup();
    renderWithProviders(<Settings />);

    await user.click(await screen.findByRole("button", { name: /^searches$/i }));
    await user.click(await screen.findByRole("button", { name: /check now/i }));

    expect(settingsMocks.checkSearch).toHaveBeenCalledWith("search-1");
  });

  it("runs Gmail sync from the integrations surface", async () => {
    const user = userEvent.setup();
    renderWithProviders(<Settings />);

    await user.click(await screen.findByRole("button", { name: /^integrations$/i }));
    await user.click(await screen.findByRole("button", { name: /sync gmail/i }));

    expect(settingsMocks.syncGoogleIntegration).toHaveBeenCalledTimes(1);
  });

  it("rejects whitespace-only API keys before calling the backend", async () => {
    const user = userEvent.setup();
    renderWithProviders(<Settings />);

    await user.click(await screen.findByRole("button", { name: /^integrations$/i }));
    const apiKeyInputs = await screen.findAllByLabelText("API key");
    await user.type(apiKeyInputs[0], "   ");
    await user.click(screen.getAllByRole("button", { name: /save key/i })[0]);

    expect(settingsMocks.upsertIntegration).not.toHaveBeenCalled();
    expect(toastMock).toHaveBeenCalledWith("error", "Enter an API key before saving");
  });

  it("hides Google sync and disconnect actions until Google is configured", async () => {
    const user = userEvent.setup();
    settingsMocks.listIntegrations.mockResolvedValueOnce({
      data: [
        {
          provider: "google",
          auth_type: "oauth",
          connected: false,
          status: "not_configured",
          masked_value: null,
          account_email: null,
          scopes: [],
          updated_at: null,
          last_validated_at: null,
          last_synced_at: null,
          last_error: null,
        },
      ],
    });

    renderWithProviders(<Settings />);

    await user.click(await screen.findByRole("button", { name: /^integrations$/i }));

    expect(await screen.findByText("Google Gmail")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /sync gmail/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /disconnect/i })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: /connect google/i })).toBeInTheDocument();
  });

  it("humanizes Google callback status codes and strips them from the URL", async () => {
    window.history.replaceState(
      {},
      "",
      "/settings?tab=integrations&integration_status=connected&integration_provider=google&integration_message=google_connected"
    );

    renderWithProviders(<Settings />);

    expect(await screen.findByRole("heading", { name: "Settings" })).toBeInTheDocument();
    expect(toastMock).toHaveBeenCalledWith("success", "Google Gmail connected.");
    expect(window.location.search).toBe("?tab=integrations");
  });
});
