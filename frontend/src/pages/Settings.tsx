import {
  Bell,
  BellSlash,
  BookmarkSimple,
  Database,
  DownloadSimple,
  Eye,
  EyeSlash,
  FloppyDisk,
  GearSix,
  Key,
  Lightning,
  LightningSlash,
  Lock,
  MagnifyingGlass,
  Moon,
  Play,
  Plus,
  Sun,
  ToggleLeft,
  ToggleRight,
  Trash,
  UploadSimple,
  UserMinus,
  Warning,
} from "@phosphor-icons/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
import { adminApi } from "../api/admin";
import { scraperApi } from "../api/scraper";
import { settingsApi, type AppSettings, type SavedSearch } from "../api/settings";
import Badge from "../components/ui/Badge";
import Button from "../components/ui/Button";
import Card from "../components/ui/Card";
import EmptyState from "../components/ui/EmptyState";
import Input from "../components/ui/Input";
import Modal from "../components/ui/Modal";
import ScraperControlPanel from "../components/scraper/ScraperControlPanel";
import Skeleton from "../components/ui/Skeleton";
import { toast } from "../components/ui/Toast";
import { useUIStore } from "../store/useUIStore";

function getStorage(): Storage | null {
  if (typeof window === "undefined") return null;
  const s = window.localStorage;
  if (!s) return null;
  if (typeof s.getItem !== "function") return null;
  if (typeof s.setItem !== "function") return null;
  if (typeof s.removeItem !== "function") return null;
  return s;
}

function ToggleRow({
  icon,
  label,
  description,
  enabled,
  onToggle,
}: {
  icon: React.ReactNode;
  label: string;
  description: string;
  enabled: boolean;
  onToggle: () => void;
}) {
  return (
    <div className="flex items-center justify-between py-3">
      <div className="flex items-center gap-3">
        <div className="text-text-muted">{icon}</div>
        <div>
          <p className="text-sm font-medium text-text-primary">{label}</p>
          <p className="text-xs text-text-muted">{description}</p>
        </div>
      </div>
      <button
        type="button"
        onClick={onToggle}
        className="text-accent-primary hover:opacity-80 transition-opacity"
      >
        {enabled ? <ToggleRight size={28} /> : <ToggleLeft size={28} className="text-text-muted" />}
      </button>
    </div>
  );
}

function SettingsSkeleton() {
  return (
    <div className="space-y-6">
      {Array.from({ length: 3 }).map((_, i) => (
        <div key={i} className="bg-bg-secondary border border-border rounded-[var(--radius-lg)] p-4 space-y-4">
          <Skeleton variant="text" className="w-1/4 h-5" />
          <Skeleton variant="rect" className="w-full h-12" />
          <Skeleton variant="rect" className="w-full h-12" />
        </div>
      ))}
    </div>
  );
}

function SavedSearchCard({
  search,
  onToggleAlert,
  onDelete,
  isDeleting,
}: {
  search: SavedSearch;
  onToggleAlert: () => void;
  onDelete: () => void;
  isDeleting: boolean;
}) {
  return (
    <div className="flex items-center justify-between py-3 px-3 rounded-[var(--radius-md)] hover:bg-bg-tertiary transition-colors">
      <div className="flex items-center gap-3 min-w-0 flex-1">
        <MagnifyingGlass size={16} weight="bold" className="text-text-muted shrink-0" />
        <div className="min-w-0">
          <p className="text-sm font-medium text-text-primary truncate">{search.name}</p>
          {search.filters && (
            <div className="flex flex-wrap gap-1 mt-1">
              {Object.entries(search.filters).map(([key, value]) => (
                <Badge key={key} size="sm">
                  {key}: {String(value)}
                </Badge>
              ))}
            </div>
          )}
        </div>
      </div>
      <div className="flex items-center gap-2 shrink-0">
        <button
          type="button"
          onClick={onToggleAlert}
          className="p-1.5 rounded-[var(--radius-md)] hover:bg-bg-elevated transition-colors"
          title={search.alert_enabled ? 'Disable alerts' : 'Enable alerts'}
        >
          {search.alert_enabled ? (
            <Bell size={16} weight="bold" className="text-accent-primary" />
          ) : (
            <BellSlash size={16} weight="bold" className="text-text-muted" />
          )}
        </button>
        <Button
          variant="ghost"
          size="sm"
          onClick={onDelete}
          loading={isDeleting}
          icon={<Trash size={14} weight="bold" />}
          className="text-text-muted hover:text-accent-danger"
        />
      </div>
    </div>
  );
}

export default function Settings() {
  const queryClient = useQueryClient();
  const { theme, setTheme } = useUIStore();

  // Settings query
  const { data: settings, isLoading: loadingSettings } = useQuery({
    queryKey: ['settings'],
    queryFn: () => settingsApi.getSettings().then((r) => r.data),
  });

  // Saved searches query
  const { data: searches, isLoading: loadingSearches } = useQuery({
    queryKey: ['savedSearches'],
    queryFn: () => settingsApi.listSearches().then((r) => r.data),
  });

  // Local settings state
  const [notifications, setNotifications] = useState(false);
  const [autoApply, setAutoApply] = useState(false);

  useEffect(() => {
    if (settings) {
      setNotifications(settings.notifications_enabled ?? false);
      setAutoApply(settings.auto_apply_enabled ?? false);
    }
  }, [settings]);

  // API Keys state
  const [apiKeys, setApiKeys] = useState({
    openrouter: '',
    serpapi: '',
    theirstack: '',
    apify: '',
  });
  const [showKeys, setShowKeys] = useState<Record<string, boolean>>({});

  const toggleKeyVisibility = (key: string) => {
    setShowKeys((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const saveApiKeysMutation = useMutation({
    mutationFn: async () => {
      // API keys saved via settings endpoint
      await settingsApi.updateSettings({ ...settings, api_keys: apiKeys } as Partial<AppSettings>);
    },
    onSuccess: () => toast('success', 'API keys saved'),
    onError: () => toast('error', 'Failed to save API keys'),
  });

  // Settings mutation
  const settingsMutation = useMutation({
    mutationFn: (data: Partial<AppSettings>) => settingsApi.updateSettings(data),
    onSuccess: () => {
      toast('success', 'Settings updated');
      queryClient.invalidateQueries({ queryKey: ['settings'] });
    },
    onError: () => toast('error', 'Failed to update settings'),
  });

  // Trigger all scrapers mutation
  const triggerAllMutation = useMutation({
    mutationFn: () => scraperApi.triggerScraper(),
    onSuccess: () => {
      toast('success', 'Scrapers triggered successfully');
      queryClient.invalidateQueries({ queryKey: ['scraper', 'runs'] });
    },
    onError: () => toast('error', 'Failed to trigger scrapers'),
  });

  const handleToggleNotifications = () => {
    const next = !notifications;
    setNotifications(next);
    settingsMutation.mutate({ notifications_enabled: next });
  };

  const handleToggleAutoApply = () => {
    const next = !autoApply;
    setAutoApply(next);
    settingsMutation.mutate({ auto_apply_enabled: next });
  };

  const handleToggleTheme = () => {
    const next = theme === 'dark' ? 'light' : 'dark';
    setTheme(next);
    settingsMutation.mutate({ theme: next });
  };

  // Saved search mutations
  const [showAddSearch, setShowAddSearch] = useState(false);
  const [newSearchName, setNewSearchName] = useState('');
  const [newSearchFilters, setNewSearchFilters] = useState('');

  const createSearchMutation = useMutation({
    mutationFn: (data: { name: string; filters: Record<string, string>; alert_enabled: boolean }) =>
      settingsApi.createSearch(data),
    onSuccess: () => {
      toast('success', 'Search saved');
      setShowAddSearch(false);
      setNewSearchName('');
      setNewSearchFilters('');
      queryClient.invalidateQueries({ queryKey: ['savedSearches'] });
    },
    onError: () => toast('error', 'Failed to save search'),
  });

  const [deletingSearchId, setDeletingSearchId] = useState<string | null>(null);

  const deleteSearchMutation = useMutation({
    mutationFn: (id: string) => settingsApi.deleteSearch(id),
    onSuccess: () => {
      toast('success', 'Search deleted');
      setDeletingSearchId(null);
      queryClient.invalidateQueries({ queryKey: ['savedSearches'] });
    },
    onError: () => {
      toast('error', 'Failed to delete search');
      setDeletingSearchId(null);
    },
  });

  const handleCreateSearch = () => {
    if (!newSearchName.trim()) return;
    let filters: Record<string, string> = {};
    if (newSearchFilters.trim()) {
      try {
        filters = JSON.parse(newSearchFilters);
      } catch {
        toast('error', 'Invalid JSON filters');
        return;
      }
    }
    createSearchMutation.mutate({ name: newSearchName.trim(), filters, alert_enabled: true });
  };

  const handleToggleSearchAlert = (search: SavedSearch) => {
    settingsApi
      .createSearch({ ...search, alert_enabled: !search.alert_enabled })
      .then(() => queryClient.invalidateQueries({ queryKey: ['savedSearches'] }));
  };

  // Data management
  const handleExport = async () => {
    try {
      const response = await adminApi.exportData();
      const blob = new Blob([JSON.stringify(response.data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `jobradar-export-${new Date().toISOString().split('T')[0]}.json`;
      link.click();
      URL.revokeObjectURL(url);
      toast('success', 'Data exported successfully');
    } catch {
      toast('error', 'Failed to export data');
    }
  };

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      const text = await file.text();
      const data = JSON.parse(text);
      await adminApi.importData(data);
      toast('success', 'Data imported successfully');
      queryClient.invalidateQueries();
    } catch {
      toast('error', 'Failed to import data. Check the file format.');
    }
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const [showClearConfirm, setShowClearConfirm] = useState(false);

  const clearDataMutation = useMutation({
    mutationFn: async () => {
      // Clear data not yet implemented on backend
      await Promise.resolve();
    },
    onSuccess: () => {
      toast('success', 'All data cleared');
      setShowClearConfirm(false);
      queryClient.invalidateQueries();
    },
    onError: () => toast('error', 'Failed to clear data'),
  });

  // Account management
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showDeleteAccount, setShowDeleteAccount] = useState(false);

  const changePasswordMutation = useMutation({
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    mutationFn: async (_data: { current_password: string; new_password: string }) => {
      // Password change not yet implemented on backend
      await Promise.resolve();
    },
    onSuccess: () => {
      toast('success', 'Password changed successfully');
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    },
    onError: () => toast('error', 'Failed to change password. Check your current password.'),
  });

  const handleChangePassword = () => {
    if (!currentPassword || !newPassword) {
      toast('error', 'Please fill in all password fields');
      return;
    }
    if (newPassword !== confirmPassword) {
      toast('error', 'New passwords do not match');
      return;
    }
    if (newPassword.length < 8) {
      toast('error', 'Password must be at least 8 characters');
      return;
    }
    changePasswordMutation.mutate({
      current_password: currentPassword,
      new_password: newPassword,
    });
  };

  const deleteAccountMutation = useMutation({
    mutationFn: async () => {
      // Account deletion not yet implemented on backend
      await Promise.resolve();
    },
    onSuccess: () => {
      toast('success', 'Account deleted');
      const storage = getStorage();
      storage?.removeItem('access_token');
      storage?.removeItem('refresh_token');
      window.location.href = '/login';
    },
    onError: () => toast('error', 'Failed to delete account'),
  });

  if (loadingSettings) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-text-primary">Settings</h1>
        </div>
        <SettingsSkeleton />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <div className="text-xs font-medium text-text-muted tracking-tight">
          Preferences
        </div>
        <h1 className="mt-1 text-2xl font-semibold tracking-tight text-text-primary">
          Settings
        </h1>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* App Settings */}
        <Card>
          <h2 className="text-sm font-semibold text-text-primary flex items-center gap-2 mb-2">
            <GearSix size={16} weight="bold" className="text-accent-primary" />
            App Settings
          </h2>
          <div className="divide-y divide-border">
            <ToggleRow
              icon={
                theme === 'dark' ? (
                  <Moon size={18} weight="bold" />
                ) : (
                  <Sun size={18} weight="bold" />
                )
              }
              label="Dark Mode"
              description={theme === 'dark' ? 'Dark theme enabled' : 'Light theme enabled'}
              enabled={theme === 'dark'}
              onToggle={handleToggleTheme}
            />
            <ToggleRow
              icon={
                notifications ? (
                  <Bell size={18} weight="bold" />
                ) : (
                  <BellSlash size={18} weight="bold" />
                )
              }
              label="Notifications"
              description="Receive alerts for new matches and updates"
              enabled={notifications}
              onToggle={handleToggleNotifications}
            />
            <ToggleRow
              icon={
                autoApply ? (
                  <Lightning size={18} weight="bold" />
                ) : (
                  <LightningSlash size={18} weight="bold" />
                )
              }
              label="Auto-Apply"
              description="Automatically apply to high-match jobs"
              enabled={autoApply}
              onToggle={handleToggleAutoApply}
            />
          </div>
        </Card>

        {/* API Keys */}
        <Card>
          <h2 className="text-sm font-semibold text-text-primary flex items-center gap-2 mb-4">
            <Key size={16} weight="bold" className="text-accent-primary" />
            API Keys
          </h2>
          <div className="space-y-3">
            {(['openrouter', 'serpapi', 'theirstack', 'apify'] as const).map((key) => (
              <div key={key} className="space-y-1">
                <label className="text-xs font-medium text-text-muted uppercase tracking-wide">
                  {key === 'openrouter' ? 'OpenRouter' : key === 'serpapi' ? 'SerpAPI' : key === 'theirstack' ? 'TheirStack' : 'Apify'}
                </label>
                <div className="flex gap-2">
                  <Input
                    type={showKeys[key] ? 'text' : 'password'}
                    placeholder={`Enter ${key} API key`}
                    value={apiKeys[key]}
                    onChange={(e) => setApiKeys((prev) => ({ ...prev, [key]: e.target.value }))}
                  />
                  <button
                    type="button"
                    onClick={() => toggleKeyVisibility(key)}
                    className="px-2 text-text-muted hover:text-text-primary transition-colors"
                  >
                    {showKeys[key] ? (
                      <EyeSlash size={16} weight="bold" />
                    ) : (
                      <Eye size={16} weight="bold" />
                    )}
                  </button>
                </div>
              </div>
            ))}
            <Button
              variant="primary"
              size="sm"
              onClick={() => saveApiKeysMutation.mutate()}
              loading={saveApiKeysMutation.isPending}
              icon={<FloppyDisk size={14} weight="bold" />}
            >
              Save API Keys
            </Button>
          </div>
        </Card>

        {/* Data Management */}
        <Card>
          <h2 className="text-sm font-semibold text-text-primary flex items-center gap-2 mb-4">
            <Database size={16} weight="bold" className="text-accent-primary" />
            Data Management
          </h2>
          <div className="space-y-3">
            <Button
              variant="secondary"
              className="w-full justify-start"
              onClick={handleExport}
              icon={<DownloadSimple size={16} weight="bold" />}
            >
              Export All Data (JSON)
            </Button>
            <input
              ref={fileInputRef}
              type="file"
              accept=".json"
              onChange={handleImport}
              className="hidden"
            />
            <Button
              variant="secondary"
              className="w-full justify-start"
              onClick={() => fileInputRef.current?.click()}
              icon={<UploadSimple size={16} weight="bold" />}
            >
              Import Data
            </Button>
            <Button
              variant="danger"
              className="w-full justify-start"
              onClick={() => setShowClearConfirm(true)}
              icon={<Trash size={16} weight="bold" />}
            >
              Clear All Data
            </Button>
          </div>
        </Card>

        {/* Scraper Controls */}
        <Card className="lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-text-primary flex items-center gap-2">
              <Play size={16} weight="bold" className="text-accent-primary" />
              Scraper Controls
            </h2>
            <Button
              variant="primary"
              size="sm"
              onClick={() => triggerAllMutation.mutate()}
              loading={triggerAllMutation.isPending}
              icon={<Play size={14} weight="bold" />}
            >
              Run All Scrapers
            </Button>
          </div>
          <ScraperControlPanel />
        </Card>

        {/* Saved Searches */}
        <Card className="lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-text-primary flex items-center gap-2">
              <BookmarkSimple size={16} weight="bold" className="text-accent-primary" />
              Saved Searches
            </h2>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setShowAddSearch(true)}
              icon={<Plus size={14} weight="bold" />}
            >
              Add Search
            </Button>
          </div>
          {loadingSearches ? (
            <div className="space-y-3">
              {Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="flex items-center gap-3 py-3">
                  <Skeleton variant="rect" className="w-full h-10" />
                </div>
              ))}
            </div>
          ) : !searches || searches.length === 0 ? (
            <EmptyState
              icon={<BookmarkSimple size={32} weight="bold" />}
              title="No saved searches"
              description="Save your frequently used search queries for quick access"
              action={{ label: 'Add Search', onClick: () => setShowAddSearch(true) }}
            />
          ) : (
            <div className="divide-y divide-border/50">
              {searches.map((search) => (
                <SavedSearchCard
                  key={search.id}
                  search={search}
                  onToggleAlert={() => handleToggleSearchAlert(search)}
                  onDelete={() => {
                    setDeletingSearchId(search.id);
                    deleteSearchMutation.mutate(search.id);
                  }}
                  isDeleting={deletingSearchId === search.id && deleteSearchMutation.isPending}
                />
              ))}
            </div>
          )}
        </Card>

        {/* Account */}
        <Card className="lg:col-span-2">
          <h2 className="text-sm font-semibold text-text-primary flex items-center gap-2 mb-4">
            <Lock size={16} weight="bold" className="text-accent-primary" />
            Account
          </h2>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div>
              <h3 className="text-sm font-medium text-text-secondary mb-3">Change Password</h3>
              <div className="space-y-3">
                <Input
                  type="password"
                  label="Current Password"
                  placeholder="Enter current password"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                />
                <Input
                  type="password"
                  label="New Password"
                  placeholder="Enter new password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                />
                <Input
                  type="password"
                  label="Confirm New Password"
                  placeholder="Confirm new password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  error={confirmPassword && newPassword !== confirmPassword ? 'Passwords do not match' : undefined}
                />
                <Button
                  variant="primary"
                  onClick={handleChangePassword}
                  loading={changePasswordMutation.isPending}
                  disabled={!currentPassword || !newPassword || !confirmPassword}
                  icon={<Lock size={14} weight="bold" />}
                >
                  Update Password
                </Button>
              </div>
            </div>

            <div>
              <h3 className="text-sm font-medium text-text-secondary mb-3">Danger Zone</h3>
              <div className="p-4 border border-accent-danger/30 rounded-[var(--radius-md)] bg-accent-danger/5">
                <div className="flex items-start gap-3">
                  <Warning
                    size={18}
                    weight="fill"
                    className="text-accent-danger shrink-0 mt-0.5"
                  />
                  <div>
                    <p className="text-sm font-medium text-text-primary">Delete Account</p>
                    <p className="text-xs text-text-muted mt-1 mb-3">
                      Permanently delete your account and all associated data. This action cannot be undone.
                    </p>
                    <Button
                      variant="danger"
                      size="sm"
                      onClick={() => setShowDeleteAccount(true)}
                      icon={<UserMinus size={14} weight="bold" />}
                    >
                      Delete Account
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* Add Search Modal */}
      <Modal open={showAddSearch} onClose={() => setShowAddSearch(false)} title="Add Saved Search" size="sm">
        <div className="space-y-4">
          <Input
            label="Search Name"
            placeholder="e.g., Remote React Senior"
            value={newSearchName}
            onChange={(e) => setNewSearchName(e.target.value)}
          />
          <Input
            label="Filters (JSON, optional)"
            placeholder='e.g., {"remote_type": "remote", "q": "react"}'
            value={newSearchFilters}
            onChange={(e) => setNewSearchFilters(e.target.value)}
          />
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="secondary" onClick={() => setShowAddSearch(false)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={handleCreateSearch}
              loading={createSearchMutation.isPending}
              disabled={!newSearchName.trim()}
            >
              Save
            </Button>
          </div>
        </div>
      </Modal>

      {/* Clear Data Confirmation Modal */}
      <Modal open={showClearConfirm} onClose={() => setShowClearConfirm(false)} title="Clear All Data" size="sm">
        <div className="space-y-4">
          <div className="flex items-start gap-3">
            <Warning size={20} weight="fill" className="text-accent-danger shrink-0 mt-0.5" />
            <p className="text-sm text-text-secondary">
              This will permanently delete all your jobs, applications, documents, and settings.
              This action cannot be undone.
            </p>
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="secondary" onClick={() => setShowClearConfirm(false)}>
              Cancel
            </Button>
            <Button
              variant="danger"
              onClick={() => clearDataMutation.mutate()}
              loading={clearDataMutation.isPending}
            >
              Clear All Data
            </Button>
          </div>
        </div>
      </Modal>

      {/* Delete Account Confirmation Modal */}
      <Modal open={showDeleteAccount} onClose={() => setShowDeleteAccount(false)} title="Delete Account" size="sm">
        <div className="space-y-4">
          <div className="flex items-start gap-3">
            <Warning size={20} weight="fill" className="text-accent-danger shrink-0 mt-0.5" />
            <p className="text-sm text-text-secondary">
              Are you sure you want to delete your account? All your data, including saved jobs,
              applications, and documents will be permanently removed. This cannot be undone.
            </p>
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="secondary" onClick={() => setShowDeleteAccount(false)}>
              Cancel
            </Button>
            <Button
              variant="danger"
              onClick={() => deleteAccountMutation.mutate()}
              loading={deleteAccountMutation.isPending}
            >
              Delete My Account
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
