import {
  CheckCircle,
  Code,
  Database,
  DownloadSimple,
  Key,
  Lock,
  MagnifyingGlass,
  PencilSimple,
  Trash,
  WarningCircle,
} from "@phosphor-icons/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";
import { adminApi } from "../api/admin";
import { changePasswordApi, deleteAccountApi } from "../api/auth";
import {
  settingsApi,
  type AppSettings,
  type IntegrationStatus,
  type SavedSearch,
} from "../api/settings";
import Badge from "../components/ui/Badge";
import Button from "../components/ui/Button";
import Input from "../components/ui/Input";
import Modal from "../components/ui/Modal";
import Select from "../components/ui/Select";
import Skeleton from "../components/ui/Skeleton";
import Textarea from "../components/ui/Textarea";
import { MetricStrip } from "../components/system/MetricStrip";
import { PageHeader } from "../components/system/PageHeader";
import { SettingsSection } from "../components/system/SettingsSection";
import { SplitWorkspace } from "../components/system/SplitWorkspace";
import { StateBlock } from "../components/system/StateBlock";
import { Surface } from "../components/system/Surface";
import { toast } from "../components/ui/toastService";
import { useAuthStore } from "../store/useAuthStore";

type SearchEditorState = {
  id: string | null;
  name: string;
  filtersText: string;
  alertEnabled: boolean;
};

type PasswordForm = {
  currentPassword: string;
  newPassword: string;
  confirmPassword: string;
};

const THEME_OPTIONS = [
  { value: "system", label: "System" },
  { value: "light", label: "Light" },
  { value: "dark", label: "Dark" },
];

const INTEGRATION_LABELS: Record<IntegrationStatus["provider"], string> = {
  openrouter: "OpenRouter",
  serpapi: "SerpAPI",
  theirstack: "TheirStack",
  apify: "Apify",
};

const INTEGRATION_NOTES: Record<IntegrationStatus["provider"], string> = {
  openrouter: "Model access for Copilot, cover letters, and summary loops.",
  serpapi: "External search coverage for broader discovery flows.",
  theirstack: "Market and company enrichment for matching and intelligence.",
  apify: "Scraper expansion and long-running automation jobs.",
};

function initialAppSettings(): AppSettings {
  return {
    theme: "system",
    notifications_enabled: true,
    auto_apply_enabled: false,
  };
}

function blankSearchEditor(): SearchEditorState {
  return {
    id: null,
    name: "",
    filtersText: JSON.stringify({}, null, 2),
    alertEnabled: true,
  };
}

function summarizeFilters(filters: Record<string, unknown>): string {
  const entries = Object.entries(filters);
  if (!entries.length) return "No filters";
  return entries
    .slice(0, 3)
    .map(([key, value]) => {
      if (Array.isArray(value)) {
        return `${key}: ${value.join(", ")}`;
      }
      if (value && typeof value === "object") {
        return `${key}: {…}`;
      }
      return `${key}: ${String(value)}`;
    })
    .join(" • ");
}

function formatCheckedAt(value: string | null): string {
  if (!value) return "Never checked";
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function parseFilters(text: string): Record<string, unknown> {
  const trimmed = text.trim();
  if (!trimmed) return {};
  const parsed = JSON.parse(trimmed);
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
    throw new Error("Saved search filters must be a JSON object");
  }
  return parsed as Record<string, unknown>;
}

export default function Settings() {
  const queryClient = useQueryClient();
  const user = useAuthStore((state) => state.user);
  const [appForm, setAppForm] = useState<AppSettings>(initialAppSettings());
  const [passwordForm, setPasswordForm] = useState<PasswordForm>({
    currentPassword: "",
    newPassword: "",
    confirmPassword: "",
  });
  const [searchEditor, setSearchEditor] = useState<SearchEditorState>(blankSearchEditor());
  const [integrationDrafts, setIntegrationDrafts] = useState<Record<string, string>>({});
  const [deleteConfirm, setDeleteConfirm] = useState("");
  const [clearConfirm, setClearConfirm] = useState("");
  const [searchModalOpen, setSearchModalOpen] = useState(false);

  const { data: settings } = useQuery({
    queryKey: ["settings", "app"],
    queryFn: () => settingsApi.getSettings().then((response) => response.data),
  });

  const { data: searches, isLoading: searchesLoading } = useQuery({
    queryKey: ["settings", "searches"],
    queryFn: () => settingsApi.listSearches().then((response) => response.data),
  });

  const { data: integrations, isLoading: integrationsLoading } = useQuery({
    queryKey: ["settings", "integrations"],
    queryFn: () => settingsApi.listIntegrations().then((response) => response.data),
  });

  useEffect(() => {
    if (settings) {
      setAppForm(settings);
    }
  }, [settings]);

  useEffect(() => {
    if (!integrations) return;
    setIntegrationDrafts((current) => {
      const next = { ...current };
      for (const integration of integrations) {
        if (!(integration.provider in next)) {
          next[integration.provider] = "";
        }
      }
      return next;
    });
  }, [integrations]);

  const connectedCount = integrations?.filter((item) => item.connected).length ?? 0;
  const alertEnabledCount = searches?.filter((item) => item.alert_enabled).length ?? 0;

  const metrics = useMemo(
    () => [
      {
        key: "searches",
        label: "Saved searches",
        value: searches?.length ?? 0,
        hint: "Named filters used for alerts and discovery.",
      },
      {
        key: "alerts",
        label: "Alerts on",
        value: alertEnabledCount,
        hint: "Saved searches currently watching for changes.",
      },
      {
        key: "integrations",
        label: "Connected integrations",
        value: connectedCount,
        hint: "Secrets stored in the dedicated integration vault.",
      },
      {
        key: "profile",
        label: "Signed in",
        value: user?.email ?? "Unknown",
        hint: "The authenticated workspace owner.",
      },
    ],
    [alertEnabledCount, connectedCount, searches?.length, user?.email]
  );

  const saveAppMutation = useMutation({
    mutationFn: (data: AppSettings) => settingsApi.updateSettings(data),
    onSuccess: (response) => {
      setAppForm(response.data);
      toast("success", "Workspace settings saved");
      queryClient.invalidateQueries({ queryKey: ["settings", "app"] });
    },
    onError: () => toast("error", "Failed to save workspace settings"),
  });

  const saveSearchMutation = useMutation({
    mutationFn: async () => {
      const filters = parseFilters(searchEditor.filtersText);
      const payload = {
        name: searchEditor.name.trim(),
        filters,
        alert_enabled: searchEditor.alertEnabled,
      };

      if (searchEditor.id) {
        return settingsApi.updateSearch(searchEditor.id, payload);
      }
      return settingsApi.createSearch(payload);
    },
    onSuccess: () => {
      toast("success", searchEditor.id ? "Saved search updated" : "Saved search created");
      setSearchEditor(blankSearchEditor());
      setSearchModalOpen(false);
      queryClient.invalidateQueries({ queryKey: ["settings", "searches"] });
    },
    onError: (error) => {
      const message = error instanceof Error ? error.message : "Failed to save search";
      toast("error", message);
    },
  });

  const deleteSearchMutation = useMutation({
    mutationFn: (id: string) => settingsApi.deleteSearch(id),
    onSuccess: () => {
      toast("success", "Saved search deleted");
      queryClient.invalidateQueries({ queryKey: ["settings", "searches"] });
    },
    onError: () => toast("error", "Failed to delete saved search"),
  });

  const integrationUpsertMutation = useMutation({
    mutationFn: async (provider: IntegrationStatus["provider"]) => {
      const key = integrationDrafts[provider]?.trim();
      if (!key) throw new Error("Enter an API key before saving");
      return settingsApi.upsertIntegration(provider, key);
    },
    onSuccess: (_response, provider) => {
      setIntegrationDrafts((current) => ({ ...current, [provider]: "" }));
      toast("success", `${INTEGRATION_LABELS[provider]} connected`);
      queryClient.invalidateQueries({ queryKey: ["settings", "integrations"] });
    },
    onError: (error) => {
      const message = error instanceof Error ? error.message : "Failed to save integration";
      toast("error", message);
    },
  });

  const integrationDeleteMutation = useMutation({
    mutationFn: (provider: IntegrationStatus["provider"]) => settingsApi.deleteIntegration(provider),
    onSuccess: (_response, provider) => {
      toast("success", `${INTEGRATION_LABELS[provider]} disconnected`);
      queryClient.invalidateQueries({ queryKey: ["settings", "integrations"] });
    },
    onError: () => toast("error", "Failed to disconnect integration"),
  });

  const changePasswordMutation = useMutation({
    mutationFn: () =>
      changePasswordApi(passwordForm.currentPassword, passwordForm.newPassword),
    onSuccess: () => {
      toast("success", "Password updated");
      setPasswordForm({ currentPassword: "", newPassword: "", confirmPassword: "" });
    },
    onError: () => toast("error", "Password update failed"),
  });

  const deleteAccountMutation = useMutation({
    mutationFn: () => deleteAccountApi(),
    onSuccess: () => {
      toast("success", "Account deletion requested");
    },
    onError: () => toast("error", "Account deletion failed"),
  });

  const clearDataMutation = useMutation({
    mutationFn: () => adminApi.clearData(),
    onSuccess: (response) => {
      toast("success", `Cleared ${response.data.rows_deleted} rows`);
      queryClient.invalidateQueries();
    },
    onError: () => toast("error", "Failed to clear data"),
  });

  async function handleExport() {
    try {
      const response = await adminApi.exportData();
      const blob = response.data;
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `jobradar-export-${new Date().toISOString().slice(0, 10)}.json`;
      anchor.click();
      URL.revokeObjectURL(url);
      toast("success", "Export started");
    } catch {
      toast("error", "Failed to export data");
    }
  }

  function openSearchEditor(search?: SavedSearch) {
    if (!search) {
      setSearchEditor(blankSearchEditor());
    } else {
      setSearchEditor({
        id: search.id,
        name: search.name,
        filtersText: JSON.stringify(search.filters ?? {}, null, 2),
        alertEnabled: search.alert_enabled,
      });
    }
    setSearchModalOpen(true);
  }

  const clearDataReady = clearConfirm.trim().toLowerCase() === "clear";
  const deleteAccountReady = deleteConfirm.trim().toLowerCase() === "delete";

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Configuration"
        title="Settings"
        description="System controls, saved-search maintenance, secret management, and account safety live here. This surface uses the real backend endpoints so changes persist instead of simulating success."
        actions={
          <>
            <Button variant="secondary" onClick={handleExport} icon={<DownloadSimple size={16} weight="bold" />}>
              Export
            </Button>
            <Button
              onClick={() => saveAppMutation.mutate(appForm)}
              loading={saveAppMutation.isPending}
              icon={<CheckCircle size={16} weight="bold" />}
            >
              Save workspace
            </Button>
          </>
        }
      />

      <MetricStrip items={metrics} />

      <SplitWorkspace
        primary={
          <div className="space-y-6">
            <SettingsSection
              title="Workspace defaults"
              description="Theme, notifications, and auto-apply controls are stored with the app settings record."
            >
              <div className="grid gap-4 md:grid-cols-3">
                <Select
                  label="Theme"
                  value={appForm.theme}
                  onChange={(event) => setAppForm((current) => ({ ...current, theme: event.target.value }))}
                  options={THEME_OPTIONS}
                />
                <Select
                  label="Notifications"
                  value={appForm.notifications_enabled ? "enabled" : "disabled"}
                  onChange={(event) =>
                    setAppForm((current) => ({
                      ...current,
                      notifications_enabled: event.target.value === "enabled",
                    }))
                  }
                  options={[
                    { value: "enabled", label: "Enabled" },
                    { value: "disabled", label: "Disabled" },
                  ]}
                />
                <Select
                  label="Auto apply"
                  value={appForm.auto_apply_enabled ? "enabled" : "disabled"}
                  onChange={(event) =>
                    setAppForm((current) => ({
                      ...current,
                      auto_apply_enabled: event.target.value === "enabled",
                    }))
                  }
                  options={[
                    { value: "enabled", label: "Enabled" },
                    { value: "disabled", label: "Disabled" },
                  ]}
                />
              </div>
            </SettingsSection>

            <SettingsSection
              title="Integrations"
              description="Secrets are stored separately from the profile and only masked values come back on read."
            >
              <div className="space-y-3">
                {integrationsLoading ? (
                  <div className="space-y-3">
                    {Array.from({ length: 4 }).map((_, index) => (
                      <Skeleton key={index} variant="rect" className="h-28 w-full" />
                    ))}
                  </div>
                ) : (
                  integrations?.map((integration) => {
                    const draft = integrationDrafts[integration.provider] ?? "";
                    return (
                      <Surface key={integration.provider} tone="default" padding="md" radius="xl">
                        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                          <div className="space-y-2">
                            <div className="flex items-center gap-2">
                              <h3 className="text-sm font-semibold tracking-[-0.01em]">
                                {INTEGRATION_LABELS[integration.provider]}
                              </h3>
                              <Badge variant={integration.connected ? "success" : "default"} size="sm">
                                {integration.status.replace("_", " ")}
                              </Badge>
                            </div>
                            <p className="max-w-2xl text-sm leading-6 text-muted-foreground">
                              {INTEGRATION_NOTES[integration.provider]}
                            </p>
                            <p className="text-xs text-muted-foreground">
                              {integration.masked_value ?? "No key saved"} ·{" "}
                              {formatCheckedAt(integration.updated_at)}
                            </p>
                          </div>

                          <div className="w-full max-w-xl space-y-3">
                            <Input
                              label="API key"
                              type="password"
                              value={draft}
                              onChange={(event) =>
                                setIntegrationDrafts((current) => ({
                                  ...current,
                                  [integration.provider]: event.target.value,
                                }))
                              }
                              placeholder={`Enter ${INTEGRATION_LABELS[integration.provider]} key`}
                            />
                            <div className="flex flex-wrap justify-end gap-2">
                              <Button
                                variant="secondary"
                                onClick={() => integrationDeleteMutation.mutate(integration.provider)}
                                loading={
                                  integrationDeleteMutation.isPending &&
                                  integrationDeleteMutation.variables === integration.provider
                                }
                                icon={<Trash size={16} weight="bold" />}
                              >
                                Disconnect
                              </Button>
                              <Button
                                onClick={() => integrationUpsertMutation.mutate(integration.provider)}
                                loading={
                                  integrationUpsertMutation.isPending &&
                                  integrationUpsertMutation.variables === integration.provider
                                }
                                icon={<Key size={16} weight="bold" />}
                              >
                                Save key
                              </Button>
                            </div>
                          </div>
                        </div>
                      </Surface>
                    );
                  })
                )}
              </div>
            </SettingsSection>

            <SettingsSection
              title="Saved searches"
              description="Update filters in place, toggle alerts, or create a new workspace search."
              actions={
                <Button onClick={() => openSearchEditor()} icon={<PencilSimple size={16} weight="bold" />}>
                  New search
                </Button>
              }
            >
              {searchesLoading ? (
                <div className="space-y-3">
                  {Array.from({ length: 3 }).map((_, index) => (
                    <Skeleton key={index} variant="rect" className="h-24 w-full" />
                  ))}
                </div>
              ) : searches && searches.length > 0 ? (
                <div className="space-y-3">
                  {searches.map((search) => (
                    <Surface key={search.id} tone="default" padding="md" radius="xl">
                      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                        <div className="space-y-2">
                          <div className="flex flex-wrap items-center gap-2">
                            <h3 className="text-sm font-semibold tracking-[-0.01em]">{search.name}</h3>
                            <Badge variant={search.alert_enabled ? "success" : "default"} size="sm">
                              {search.alert_enabled ? "Alerts on" : "Alerts off"}
                            </Badge>
                          </div>
                          <p className="max-w-3xl text-sm leading-6 text-muted-foreground">
                            {summarizeFilters(search.filters)}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            Last checked {formatCheckedAt(search.last_checked_at)}
                          </p>
                        </div>
                        <div className="flex flex-wrap gap-2">
                          <Button
                            variant="secondary"
                            onClick={() =>
                              settingsApi
                                .updateSearch(search.id, {
                                  alert_enabled: !search.alert_enabled,
                                })
                                .then(() => {
                                  toast("success", "Saved search updated");
                                  queryClient.invalidateQueries({ queryKey: ["settings", "searches"] });
                                })
                                .catch(() => toast("error", "Failed to toggle alerts"))
                            }
                            icon={<CheckCircle size={16} weight="bold" />}
                          >
                            Toggle
                          </Button>
                          <Button
                            variant="secondary"
                            onClick={() => openSearchEditor(search)}
                            icon={<PencilSimple size={16} weight="bold" />}
                          >
                            Edit
                          </Button>
                          <Button
                            variant="danger"
                            onClick={() => deleteSearchMutation.mutate(search.id)}
                            loading={
                              deleteSearchMutation.isPending &&
                              deleteSearchMutation.variables === search.id
                            }
                            icon={<Trash size={16} weight="bold" />}
                          >
                            Delete
                          </Button>
                        </div>
                      </div>
                    </Surface>
                  ))}
                </div>
              ) : (
                <StateBlock
                  tone="muted"
                  title="No saved searches yet"
                  description="Create your first search to turn discovery filters into a reusable alert source."
                  icon={<MagnifyingGlass size={18} weight="bold" />}
                  action={
                    <Button onClick={() => openSearchEditor()} icon={<PencilSimple size={16} weight="bold" />}>
                      Create search
                    </Button>
                  }
                />
              )}
            </SettingsSection>

            <SettingsSection
              title="Security and data"
              description="Password changes, destructive cleanup, and data export all use the real backend."
            >
              <div className="grid gap-6 lg:grid-cols-2">
                <Surface tone="default" padding="md" radius="xl">
                  <div className="space-y-4">
                    <div className="flex items-center gap-2">
                      <Lock size={16} weight="bold" className="text-muted-foreground" />
                      <h3 className="text-sm font-semibold tracking-[-0.01em]">Change password</h3>
                    </div>
                    <Input
                      label="Current password"
                      type="password"
                      value={passwordForm.currentPassword}
                      onChange={(event) =>
                        setPasswordForm((current) => ({ ...current, currentPassword: event.target.value }))
                      }
                    />
                    <Input
                      label="New password"
                      type="password"
                      value={passwordForm.newPassword}
                      onChange={(event) =>
                        setPasswordForm((current) => ({ ...current, newPassword: event.target.value }))
                      }
                    />
                    <Input
                      label="Confirm password"
                      type="password"
                      value={passwordForm.confirmPassword}
                      onChange={(event) =>
                        setPasswordForm((current) => ({ ...current, confirmPassword: event.target.value }))
                      }
                    />
                    <Button
                      variant="secondary"
                      onClick={() => {
                        if (passwordForm.newPassword !== passwordForm.confirmPassword) {
                          toast("error", "Passwords do not match");
                          return;
                        }
                        changePasswordMutation.mutate();
                      }}
                      loading={changePasswordMutation.isPending}
                      icon={<Key size={16} weight="bold" />}
                    >
                      Update password
                    </Button>
                  </div>
                </Surface>

                <Surface tone="default" padding="md" radius="xl">
                  <div className="space-y-4">
                    <div className="flex items-center gap-2">
                      <Database size={16} weight="bold" className="text-muted-foreground" />
                      <h3 className="text-sm font-semibold tracking-[-0.01em]">Data management</h3>
                    </div>
                    <p className="text-sm leading-6 text-muted-foreground">
                      Export the workspace before any destructive action. Clear data removes the current
                      user rows and delete account removes the profile itself.
                    </p>

                    <div className="flex flex-wrap gap-2">
                      <Button variant="secondary" onClick={handleExport} icon={<DownloadSimple size={16} weight="bold" />}>
                        Export data
                      </Button>
                      <Button
                        variant="danger"
                        onClick={() => clearDataMutation.mutate()}
                        loading={clearDataMutation.isPending}
                        icon={<WarningCircle size={16} weight="bold" />}
                        disabled={!clearDataReady}
                      >
                        Clear data
                      </Button>
                    </div>

                    <Input
                      label='Type "clear" to enable the clear-data action'
                      value={clearConfirm}
                      onChange={(event) => setClearConfirm(event.target.value)}
                      placeholder="clear"
                    />

                    <div className="border-t border-border/70 pt-4">
                      <div className="mb-3 flex items-center gap-2">
                        <Trash size={16} weight="bold" className="text-accent-danger" />
                        <h4 className="text-sm font-semibold tracking-[-0.01em]">Delete account</h4>
                      </div>
                      <p className="mb-3 text-sm leading-6 text-muted-foreground">
                        This uses the real auth endpoint and should only be used when the account should be
                        removed permanently.
                      </p>
                      <Input
                        label='Type "delete" to enable account deletion'
                        value={deleteConfirm}
                        onChange={(event) => setDeleteConfirm(event.target.value)}
                        placeholder="delete"
                      />
                      <Button
                        className="mt-3"
                        variant="danger"
                        onClick={() => deleteAccountMutation.mutate()}
                        loading={deleteAccountMutation.isPending}
                        disabled={!deleteAccountReady}
                        icon={<Trash size={16} weight="bold" />}
                      >
                        Delete account
                      </Button>
                    </div>
                  </div>
                </Surface>
              </div>
            </SettingsSection>
          </div>
        }
        secondary={
          <div className="space-y-4">
            <StateBlock
              tone="muted"
              icon={<CheckCircle size={18} weight="bold" />}
              title="Operational note"
              description="Saved searches and integration secrets are now backed by real endpoints. Editing them here affects the live workspace."
            />
            <StateBlock
              tone="neutral"
              icon={<Code size={18} weight="bold" />}
              title="Current owner"
              description={user?.email ?? "No signed-in user detected"}
            />
            <StateBlock
              tone="warning"
              icon={<WarningCircle size={18} weight="bold" />}
              title="Destructive actions"
              description="Clear data and delete account require explicit typed confirmation before they are enabled."
            />
          </div>
        }
      />

      <Modal
        open={searchModalOpen}
        onClose={() => setSearchModalOpen(false)}
        title={searchEditor.id ? "Edit saved search" : "Create saved search"}
        size="lg"
      >
        <div className="space-y-4">
          <Input
            label="Name"
            value={searchEditor.name}
            onChange={(event) => setSearchEditor((current) => ({ ...current, name: event.target.value }))}
            placeholder="Frontend roles in New York"
          />
          <Textarea
            label="Filters JSON"
            value={searchEditor.filtersText}
            onChange={(event) => setSearchEditor((current) => ({ ...current, filtersText: event.target.value }))}
            className="min-h-[220px] font-mono text-sm"
          />
          <label className="flex items-center gap-2 text-sm text-muted-foreground">
            <input
              type="checkbox"
              checked={searchEditor.alertEnabled}
              onChange={(event) =>
                setSearchEditor((current) => ({ ...current, alertEnabled: event.target.checked }))
              }
              className="size-4 rounded border-border bg-bg-secondary"
            />
            Alert when this search changes
          </label>
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setSearchModalOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={() => saveSearchMutation.mutate()}
              loading={saveSearchMutation.isPending}
              icon={<CheckCircle size={16} weight="bold" />}
            >
              Save search
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
