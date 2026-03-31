import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { settingsApi, type AppSettings } from "../api/settings";
import { SettingsPageHeader } from "../components/settings/SettingsPageHeader";
import { SettingsSearchEditorModal } from "../components/settings/SettingsSearchEditorModal";
import {
  SETTINGS_TABS,
  createInitialAppSettings,
  normalizeAppSettings,
} from "../components/settings/settingsPageState";
import { useAuthStore } from "../store/useAuthStore";
import { parseThemePreference, serializeThemePreference, type ThemeFamily, type ThemeMode, useUIStore } from "../store/useUIStore";
import { SettingsTabNav, type SettingsTab } from "../components/settings/SettingsTabNav";
import { SettingsTabPanels } from "../components/settings/SettingsTabPanels";
import { toast } from "../components/ui/toastService";
import { useSettingsDataActions } from "../components/settings/useSettingsDataActions";
import { useSettingsIntegrations } from "../components/settings/useSettingsIntegrations";
import { useSettingsSearches } from "../components/settings/useSettingsSearches";
import { useSettingsSecurity } from "../components/settings/useSettingsSecurity";

export default function Settings() {
  const queryClient = useQueryClient();
  const user = useAuthStore((state) => state.user);
  const mode = useUIStore((state) => state.mode);
  const themeFamily = useUIStore((state) => state.themeFamily);
  const setThemePreference = useUIStore((state) => state.setThemePreference);

  const [appForm, setAppForm] = useState<AppSettings>(createInitialAppSettings());
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

  const {
    searchEditor,
    searchModalOpen,
    checkingSearchId,
    isSavingSearch,
    openSearchEditor,
    closeSearchEditor,
    updateSearchName,
    updateSearchFilters,
    updateSearchAlertEnabled,
    saveSearch,
    checkSearch,
    deleteSearch,
    toggleSearch,
  } = useSettingsSearches();
  const {
    integrationDrafts,
    savingProvider,
    deletingProvider,
    syncingGoogle,
    updateIntegrationDraft,
    saveIntegration,
    deleteIntegration,
    connectGoogle,
    syncGoogle,
  } = useSettingsIntegrations({ integrations, setActiveTab });
  const {
    passwordForm,
    passwordPending,
    setCurrentPassword,
    setNewPassword,
    setConfirmPassword,
    submitPasswordChange,
  } = useSettingsSecurity();
  const {
    clearConfirm,
    deleteConfirm,
    clearReady,
    deleteReady,
    clearPending,
    deletePending,
    setClearConfirm,
    setDeleteConfirm,
    exportData,
    clearData,
    deleteAccount,
  } = useSettingsDataActions();

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

  return (
    <div className="flex h-full flex-col gap-6 px-4 py-4 sm:px-6 lg:px-8">
      <SettingsPageHeader
        onSave={() => saveAppMutation.mutate(appForm)}
        isSaving={saveAppMutation.isPending}
      />

      <div className="flex flex-col gap-6 md:flex-row">
        <SettingsTabNav
          className="w-full shrink-0 md:w-64"
          tabs={SETTINGS_TABS}
          activeTab={activeTab}
          onSelect={setActiveTab}
        />

        <div className="min-w-0 flex-1 space-y-6 pb-12">
          <SettingsTabPanels
            activeTab={activeTab}
            userEmail={user?.email}
            displayName={user?.display_name}
            mode={mode}
            themeFamily={themeFamily}
            appForm={appForm}
            passwordForm={passwordForm}
            integrations={integrations}
            searches={searches}
            searchesLoading={searchesLoading}
            integrationsLoading={integrationsLoading}
            integrationDrafts={integrationDrafts}
            checkingSearchId={checkingSearchId}
            clearConfirm={clearConfirm}
            deleteConfirm={deleteConfirm}
            clearReady={clearReady}
            deleteReady={deleteReady}
            clearPending={clearPending}
            deletePending={deletePending}
            passwordPending={passwordPending}
            savingProvider={savingProvider}
            deletingProvider={deletingProvider}
            syncingGoogle={syncingGoogle}
            onModeChange={(nextMode) => updateThemeSelection({ mode: nextMode })}
            onThemeFamilyChange={(nextFamily) => updateThemeSelection({ themeFamily: nextFamily })}
            onNotificationsChange={(checked) =>
              setAppForm((current) => ({ ...current, notifications_enabled: checked }))
            }
            onAutoApplyChange={(checked) =>
              setAppForm((current) => ({ ...current, auto_apply_enabled: checked }))
            }
            onCurrentPasswordChange={setCurrentPassword}
            onNewPasswordChange={setNewPassword}
            onConfirmPasswordChange={setConfirmPassword}
            onPasswordSubmit={submitPasswordChange}
            onIntegrationDraftChange={updateIntegrationDraft}
            onIntegrationSave={saveIntegration}
            onIntegrationDelete={deleteIntegration}
            onGoogleConnect={connectGoogle}
            onGoogleSync={syncGoogle}
            onCreateSearch={() => openSearchEditor()}
            onEditSearch={(search) => openSearchEditor(search)}
            onToggleSearch={toggleSearch}
            onCheckSearch={checkSearch}
            onDeleteSearch={deleteSearch}
            onClearConfirmChange={setClearConfirm}
            onDeleteConfirmChange={setDeleteConfirm}
            onExport={exportData}
            onClear={clearData}
            onDelete={deleteAccount}
          />
        </div>
      </div>

      <SettingsSearchEditorModal
        open={searchModalOpen}
        searchEditor={searchEditor}
        saving={isSavingSearch}
        onClose={closeSearchEditor}
        onNameChange={updateSearchName}
        onFiltersChange={updateSearchFilters}
        onAlertEnabledChange={updateSearchAlertEnabled}
        onSave={saveSearch}
      />
    </div>
  );
}
