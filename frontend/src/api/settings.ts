import apiClient from './client';

export interface SavedSearch {
  id: string;
  name: string;
  filters: Record<string, string>;
  alert_enabled: boolean;
  created_at: string;
}

export interface AppSettings {
  theme: string;
  notifications_enabled: boolean;
  auto_apply_enabled: boolean;
}

export const settingsApi = {
  // Used by pages
  listSearches: () =>
    apiClient.get<SavedSearch[]>('/settings/searches'),
  createSearch: (data: { name: string; filters: Record<string, string>; alert_enabled?: boolean }) =>
    apiClient.post<SavedSearch>('/settings/searches', data),
  deleteSearch: (id: string) =>
    apiClient.delete(`/settings/searches/${id}`),
  getSettings: () =>
    apiClient.get<AppSettings>('/settings/app'),
  updateSettings: (data: Partial<AppSettings>) =>
    apiClient.patch<AppSettings>('/settings/app', data),
  // Spec aliases (point to the real endpoints)
  get: () =>
    apiClient.get<AppSettings>('/settings/app'),
  update: (data: Partial<AppSettings>) =>
    apiClient.patch<AppSettings>('/settings/app', data),
  savedSearches: () =>
    apiClient.get<SavedSearch[]>('/settings/searches'),
  createSavedSearch: (data: { name: string; filters: Record<string, unknown>; alert_enabled?: boolean }) =>
    apiClient.post<SavedSearch>('/settings/searches', data),
  deleteSavedSearch: (id: string) =>
    apiClient.delete(`/settings/searches/${id}`),
};
