import { Bell, CheckCircle, HardDrive, MagnifyingGlass, Palette, Plug, Shield, UserCircle } from "@phosphor-icons/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { adminApi } from "../api/admin";
import { changePasswordApi, deleteAccountApi } from "../api/auth";
import { settingsApi, type AppSettings, type IntegrationStatus, type SavedSearch } from "../api/settings";
import Button from "../components/ui/Button";
import Input from "../components/ui/Input";
import Modal from "../components/ui/Modal";
import Textarea from "../components/ui/Textarea";
import { toast } from "../components/ui/toastService";
import { useAuthStore } from "../store/useAuthStore";
import { parseThemePreference, serializeThemePreference, type ThemeFamily, type ThemeMode, useUIStore } from "../store/useUIStore";
import { SettingsTabNav, type SettingsTab } from "../components/settings/SettingsTabNav";
import {
  SettingsProfileSection,
  SettingsAppearanceSection,
  SettingsWorkspaceSection,
  SettingsSecuritySection,
  SettingsIntegrationsSection,
  SettingsSearchesSection,
  SettingsDataSection,
} from "../components/settings/SettingsSections";

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

const SETTINGS_TABS: Array<{
  id: SettingsTab;
  label: string;
  icon: typeof UserCircle;
}> = [
  { id: "profile", label: "Profile", icon: UserCircle },
  { id: "appearance", label: "Appearance", icon: Palette },
  { id: "workspace", label: "Workspace", icon: Bell },
  { id: "security", label: "Security", icon: Shield },
  { id: "integrations", label: "Integrations", icon: Plug },
  { id: "searches", label: "Searches", icon: MagnifyingGlass },
  { id: "data", label: "Data", icon: HardDrive },
];

const initialAppSettings = (): AppSettings => ({
  theme: "dark",
  notifications_enabled: true,
  auto_apply_enabled: false,
});

const blankSearchEditor = (): SearchEditorState => ({
  id: null,
  name: "",
  filtersText: JSON.stringify({}, null, 2),
  alertEnabled: true,
});

function normalizeAppSettings(settings: AppSettings): AppSettings {
  const { mode, themeFamily } = parseThemePreference(settings.theme);
  return {
    ...settings,
    theme: serializeThemePreference(themeFamily, mode),
  };
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
  const mode = useUIStore((state) => state.mode);
  const themeFamily = useUIStore((state) => state.themeFamily);
  const setThemePreference = useUIStore((state) => state.setThemePreference);

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
  const [activeTab, setActiveTab] = useState<SettingsTab>("profile");

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
    if (!settings) return;
    const normalized = normalizeAppSettings(settings);
    setAppForm({
      ...normalized,
      theme: serializeThemePreference(themeFamily, mode),
    });
  }, [mode, settings, themeFamily]);

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

  function updateThemeSelection(next: Partial<{ mode: ThemeMode; themeFamily: ThemeFamily }>) {
    const resolvedMode = next.mode ?? mode;
    const resolvedThemeFamily = next.themeFamily ?? themeFamily;
    setThemePreference(resolvedThemeFamily, resolvedMode);
    setAppForm((current) => ({
      ...current,
      theme: serializeThemePreference(resolvedThemeFamily, resolvedMode),
    }));
  }

  const saveAppMutation = useMutation({
    mutationFn: (data: AppSettings) => settingsApi.updateSettings(data),
    onSuccess: (response) => {
      const normalized = normalizeAppSettings(response.data);
      setAppForm(normalized);
      const nextTheme = parseThemePreference(normalized.theme);
      setThemePreference(nextTheme.themeFamily, nextTheme.mode);
      toast("success", "Settings saved");
      queryClient.invalidateQueries({ queryKey: ["settings", "app"] });
    },
    onError: () => toast("error", "Failed to save settings"),
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
      toast("success", searchEditor.id ? "Search updated" : "Search created");
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
      toast("success", "Search deleted");
      queryClient.invalidateQueries({ queryKey: ["settings", "searches"] });
    },
    onError: () => toast("error", "Failed to delete search"),
  });

  const integrationUpsertMutation = useMutation({
    mutationFn: async (provider: IntegrationStatus["provider"]) => {
      const key = integrationDrafts[provider]?.trim();
      if (!key) throw new Error("Enter an API key before saving");
      return settingsApi.upsertIntegration(provider, key);
    },
    onSuccess: (_response, provider) => {
      setIntegrationDrafts((current) => ({ ...current, [provider]: "" }));
      toast("success", `${provider} connected`);
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
      toast("success", `${provider} disconnected`);
      queryClient.invalidateQueries({ queryKey: ["settings", "integrations"] });
    },
    onError: () => toast("error", "Failed to disconnect integration"),
  });

  const changePasswordMutation = useMutation({
    mutationFn: () => changePasswordApi(passwordForm.currentPassword, passwordForm.newPassword),
    onSuccess: () => {
      toast("success", "Password updated");
      setPasswordForm({ currentPassword: "", newPassword: "", confirmPassword: "" });
    },
    onError: () => toast("error", "Password update failed"),
  });

  const deleteAccountMutation = useMutation({
    mutationFn: () => deleteAccountApi(),
    onSuccess: () => toast("success", "Account deletion requested"),
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

  function submitPasswordChange() {
    if (passwordForm.newPassword !== passwordForm.confirmPassword) {
      toast("error", "Passwords do not match");
      return;
    }
    changePasswordMutation.mutate();
  }

  const clearDataReady = clearConfirm.trim().toLowerCase() === "clear";
  const deleteAccountReady = deleteConfirm.trim().toLowerCase() === "delete";

  return (
    <div className="flex h-full flex-col gap-6 px-4 py-4 sm:px-6 lg:px-8">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="command-label mb-1">Operations</p>
          <h1 className="font-headline text-3xl font-black uppercase tracking-tight">Settings</h1>
          <p className="mt-2 text-sm text-muted-foreground">Account, theme, integrations, and saved searches.</p>
        </div>
        <Button
          variant="primary"
          onClick={() => saveAppMutation.mutate(appForm)}
          loading={saveAppMutation.isPending}
          icon={<CheckCircle size={16} weight="bold" />}
        >
          Save changes
        </Button>
      </div>

      <div className="flex flex-col gap-6 md:flex-row">
        <SettingsTabNav
          className="w-full shrink-0 md:w-64"
          tabs={SETTINGS_TABS}
          activeTab={activeTab}
          onSelect={setActiveTab}
        />

        <div className="min-w-0 flex-1 space-y-6 pb-12">
          {activeTab === "profile" ? (
            <SettingsProfileSection userEmail={user?.email} displayName={user?.display_name} />
          ) : null}

          {activeTab === "appearance" ? (
            <SettingsAppearanceSection
              mode={mode}
              themeFamily={themeFamily}
              onModeChange={(nextMode) => updateThemeSelection({ mode: nextMode })}
              onThemeFamilyChange={(nextFamily) => updateThemeSelection({ themeFamily: nextFamily })}
            />
          ) : null}

          {activeTab === "workspace" ? (
            <SettingsWorkspaceSection
              notificationsEnabled={appForm.notifications_enabled}
              autoApplyEnabled={appForm.auto_apply_enabled}
              onNotificationsChange={(checked) =>
                setAppForm((current) => ({ ...current, notifications_enabled: checked }))
              }
              onAutoApplyChange={(checked) =>
                setAppForm((current) => ({ ...current, auto_apply_enabled: checked }))
              }
            />
          ) : null}

          {activeTab === "security" ? (
            <SettingsSecuritySection
              userEmail={user?.email}
              currentPassword={passwordForm.currentPassword}
              newPassword={passwordForm.newPassword}
              confirmPassword={passwordForm.confirmPassword}
              onCurrentPasswordChange={(value) =>
                setPasswordForm((current) => ({ ...current, currentPassword: value }))
              }
              onNewPasswordChange={(value) =>
                setPasswordForm((current) => ({ ...current, newPassword: value }))
              }
              onConfirmPasswordChange={(value) =>
                setPasswordForm((current) => ({ ...current, confirmPassword: value }))
              }
              onSubmit={submitPasswordChange}
              isPending={changePasswordMutation.isPending}
            />
          ) : null}

          {activeTab === "integrations" ? (
            <SettingsIntegrationsSection
              userEmail={user?.email}
              integrations={integrations}
              drafts={integrationDrafts}
              loading={integrationsLoading}
              onDraftChange={(provider, value) =>
                setIntegrationDrafts((current) => ({ ...current, [provider]: value }))
              }
              onSave={(provider) => integrationUpsertMutation.mutate(provider)}
              onDelete={(provider) => integrationDeleteMutation.mutate(provider)}
              savingProvider={integrationUpsertMutation.variables ?? null}
              deletingProvider={integrationDeleteMutation.variables ?? null}
            />
          ) : null}

          {activeTab === "searches" ? (
            <SettingsSearchesSection
              searches={searches}
              loading={searchesLoading}
              onCreate={() => openSearchEditor()}
              onEdit={(search) => openSearchEditor(search)}
              onToggle={(search) =>
                settingsApi
                  .updateSearch(search.id, { alert_enabled: !search.alert_enabled })
                  .then(() => {
                    toast("success", "Search updated");
                    queryClient.invalidateQueries({ queryKey: ["settings", "searches"] });
                  })
                  .catch(() => toast("error", "Failed to update search"))
              }
              onDelete={(search) => deleteSearchMutation.mutate(search.id)}
            />
          ) : null}

          {activeTab === "data" ? (
            <SettingsDataSection
              clearConfirm={clearConfirm}
              deleteConfirm={deleteConfirm}
              onClearConfirmChange={setClearConfirm}
              onDeleteConfirmChange={setDeleteConfirm}
              onExport={handleExport}
              onClear={() => clearDataMutation.mutate()}
              onDelete={() => deleteAccountMutation.mutate()}
              clearReady={clearDataReady}
              deleteReady={deleteAccountReady}
              clearPending={clearDataMutation.isPending}
              deletePending={deleteAccountMutation.isPending}
            />
          ) : null}
        </div>
      </div>

      <Modal
        open={searchModalOpen}
        onClose={() => setSearchModalOpen(false)}
        title={searchEditor.id ? "Edit saved search" : "Create saved search"}
        size="lg"
        className="!rounded-none !border-2 !border-[var(--color-text-primary)] !bg-[var(--color-bg-secondary)] !shadow-none"
      >
        <div className="space-y-4">
          <Input
            label="Name"
            value={searchEditor.name}
            onChange={(event) =>
              setSearchEditor((current) => ({
                ...current,
                name: event.target.value,
              }))
            }
            placeholder="Frontend roles in New York"
          />
          <Textarea
            label="Filters JSON"
            value={searchEditor.filtersText}
            onChange={(event) =>
              setSearchEditor((current) => ({
                ...current,
                filtersText: event.target.value,
              }))
            }
            className="min-h-[220px] font-mono text-sm"
          />
          <label className="flex items-center gap-2 text-sm text-muted-foreground">
            <input
              type="checkbox"
              checked={searchEditor.alertEnabled}
              onChange={(event) =>
                setSearchEditor((current) => ({
                  ...current,
                  alertEnabled: event.target.checked,
                }))
              }
              className="size-4 rounded-none border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-secondary)] accent-[var(--color-accent-primary)]"
            />
            Alert when this search changes
          </label>
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setSearchModalOpen(false)}>
              Cancel
            </Button>
            <Button onClick={() => saveSearchMutation.mutate()} loading={saveSearchMutation.isPending} icon={<CheckCircle size={16} weight="bold" />}>
              Save search
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
