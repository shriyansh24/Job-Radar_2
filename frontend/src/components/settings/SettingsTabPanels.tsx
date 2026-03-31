import type { AppSettings, IntegrationProvider, IntegrationStatus, SavedSearch } from "../../api/settings";
import type { ThemeFamily, ThemeMode } from "../../store/useUIStore";
import {
  SettingsAppearanceSection,
  SettingsDataSection,
  SettingsIntegrationsSection,
  SettingsProfileSection,
  SettingsSearchesSection,
  SettingsSecuritySection,
  SettingsWorkspaceSection,
} from "./SettingsSections";
import type { SettingsTab } from "./SettingsTabNav";

type PasswordForm = {
  currentPassword: string;
  newPassword: string;
  confirmPassword: string;
};

type SettingsTabPanelsProps = {
  activeTab: SettingsTab;
  userEmail?: string | null;
  displayName?: string | null;
  mode: ThemeMode;
  themeFamily: ThemeFamily;
  appForm: AppSettings;
  passwordForm: PasswordForm;
  integrations?: IntegrationStatus[] | null;
  searches?: SavedSearch[] | null;
  searchesLoading: boolean;
  integrationsLoading: boolean;
  integrationDrafts: Record<string, string>;
  checkingSearchId: string | null;
  clearConfirm: string;
  deleteConfirm: string;
  clearReady: boolean;
  deleteReady: boolean;
  clearPending: boolean;
  deletePending: boolean;
  passwordPending: boolean;
  savingProvider: IntegrationStatus["provider"] | null;
  deletingProvider: IntegrationStatus["provider"] | null;
  syncingGoogle: boolean;
  onModeChange: (mode: ThemeMode) => void;
  onThemeFamilyChange: (themeFamily: ThemeFamily) => void;
  onNotificationsChange: (checked: boolean) => void;
  onAutoApplyChange: (checked: boolean) => void;
  onCurrentPasswordChange: (value: string) => void;
  onNewPasswordChange: (value: string) => void;
  onConfirmPasswordChange: (value: string) => void;
  onPasswordSubmit: () => void;
  onIntegrationDraftChange: (provider: IntegrationProvider, value: string) => void;
  onIntegrationSave: (provider: Exclude<IntegrationProvider, "google">) => void;
  onIntegrationDelete: (provider: IntegrationProvider) => void;
  onGoogleConnect: () => void;
  onGoogleSync: () => void;
  onCreateSearch: () => void;
  onEditSearch: (search: SavedSearch) => void;
  onToggleSearch: (search: SavedSearch) => void;
  onCheckSearch: (search: SavedSearch) => void;
  onDeleteSearch: (search: SavedSearch) => void;
  onClearConfirmChange: (value: string) => void;
  onDeleteConfirmChange: (value: string) => void;
  onExport: () => void;
  onClear: () => void;
  onDelete: () => void;
};

function SettingsTabPanels({
  activeTab,
  userEmail,
  displayName,
  mode,
  themeFamily,
  appForm,
  passwordForm,
  integrations,
  searches,
  searchesLoading,
  integrationsLoading,
  integrationDrafts,
  checkingSearchId,
  clearConfirm,
  deleteConfirm,
  clearReady,
  deleteReady,
  clearPending,
  deletePending,
  passwordPending,
  savingProvider,
  deletingProvider,
  syncingGoogle,
  onModeChange,
  onThemeFamilyChange,
  onNotificationsChange,
  onAutoApplyChange,
  onCurrentPasswordChange,
  onNewPasswordChange,
  onConfirmPasswordChange,
  onPasswordSubmit,
  onIntegrationDraftChange,
  onIntegrationSave,
  onIntegrationDelete,
  onGoogleConnect,
  onGoogleSync,
  onCreateSearch,
  onEditSearch,
  onToggleSearch,
  onCheckSearch,
  onDeleteSearch,
  onClearConfirmChange,
  onDeleteConfirmChange,
  onExport,
  onClear,
  onDelete,
}: SettingsTabPanelsProps) {
  if (activeTab === "profile") {
    return <SettingsProfileSection userEmail={userEmail} displayName={displayName} />;
  }

  if (activeTab === "appearance") {
    return (
      <SettingsAppearanceSection
        mode={mode}
        themeFamily={themeFamily}
        onModeChange={onModeChange}
        onThemeFamilyChange={onThemeFamilyChange}
      />
    );
  }

  if (activeTab === "workspace") {
    return (
      <SettingsWorkspaceSection
        notificationsEnabled={appForm.notifications_enabled}
        autoApplyEnabled={appForm.auto_apply_enabled}
        onNotificationsChange={onNotificationsChange}
        onAutoApplyChange={onAutoApplyChange}
      />
    );
  }

  if (activeTab === "security") {
    return (
      <SettingsSecuritySection
        userEmail={userEmail}
        currentPassword={passwordForm.currentPassword}
        newPassword={passwordForm.newPassword}
        confirmPassword={passwordForm.confirmPassword}
        onCurrentPasswordChange={onCurrentPasswordChange}
        onNewPasswordChange={onNewPasswordChange}
        onConfirmPasswordChange={onConfirmPasswordChange}
        onSubmit={onPasswordSubmit}
        isPending={passwordPending}
      />
    );
  }

  if (activeTab === "integrations") {
    return (
      <SettingsIntegrationsSection
        userEmail={userEmail}
        integrations={integrations}
        drafts={integrationDrafts}
        loading={integrationsLoading}
        onDraftChange={onIntegrationDraftChange}
        onSave={onIntegrationSave}
        onDelete={onIntegrationDelete}
        onConnectGoogle={onGoogleConnect}
        onSyncGoogle={onGoogleSync}
        savingProvider={savingProvider}
        deletingProvider={deletingProvider}
        syncingGoogle={syncingGoogle}
      />
    );
  }

  if (activeTab === "searches") {
    return (
      <SettingsSearchesSection
        searches={searches}
        loading={searchesLoading}
        checkingSearchId={checkingSearchId}
        onCreate={onCreateSearch}
        onEdit={(search) => {
          if (search) {
            onEditSearch(search);
          }
        }}
        onToggle={onToggleSearch}
        onCheck={onCheckSearch}
        onDelete={onDeleteSearch}
      />
    );
  }

  if (activeTab === "data") {
    return (
      <SettingsDataSection
        clearConfirm={clearConfirm}
        deleteConfirm={deleteConfirm}
        onClearConfirmChange={onClearConfirmChange}
        onDeleteConfirmChange={onDeleteConfirmChange}
        onExport={onExport}
        onClear={onClear}
        onDelete={onDelete}
        clearReady={clearReady}
        deleteReady={deleteReady}
        clearPending={clearPending}
        deletePending={deletePending}
      />
    );
  }

  return null;
}

export { SettingsTabPanels };
export type { PasswordForm, SettingsTabPanelsProps };
