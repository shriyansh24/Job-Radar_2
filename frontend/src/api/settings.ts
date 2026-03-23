import apiClient from './client';

export interface SavedSearch {
  id: string;
  name: string;
  filters: Record<string, unknown>;
  alert_enabled: boolean;
  last_checked_at: string | null;
  created_at: string;
}

export interface AppSettings {
  theme: string;
  notifications_enabled: boolean;
  auto_apply_enabled: boolean;
}

export interface IntegrationStatus {
  provider: 'openrouter' | 'serpapi' | 'theirstack' | 'apify';
  connected: boolean;
  status: 'connected' | 'not_configured';
  masked_value: string | null;
  updated_at: string | null;
}

export const settingsApi = {
  // Used by pages
  listSearches: () =>
    apiClient.get<SavedSearch[]>('/settings/searches'),
  createSearch: (data: { name: string; filters: Record<string, unknown>; alert_enabled?: boolean }) =>
    apiClient.post<SavedSearch>('/settings/searches', data),
  updateSearch: (
    id: string,
    data: Partial<Pick<SavedSearch, 'name' | 'filters' | 'alert_enabled'>>
  ) => apiClient.patch<SavedSearch>(`/settings/searches/${id}`, data),
  deleteSearch: (id: string) =>
    apiClient.delete(`/settings/searches/${id}`),
  listIntegrations: () =>
    apiClient.get<IntegrationStatus[]>('/settings/integrations'),
  upsertIntegration: (
    provider: IntegrationStatus['provider'],
    apiKey: string
  ) => apiClient.put<IntegrationStatus>(`/settings/integrations/${provider}`, { api_key: apiKey }),
  deleteIntegration: (provider: IntegrationStatus['provider']) =>
    apiClient.delete(`/settings/integrations/${provider}`),
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
  updateSavedSearch: (
    id: string,
    data: Partial<Pick<SavedSearch, 'name' | 'filters' | 'alert_enabled'>>
  ) => apiClient.patch<SavedSearch>(`/settings/searches/${id}`, data),
  deleteSavedSearch: (id: string) =>
    apiClient.delete(`/settings/searches/${id}`),
  integrations: () =>
    apiClient.get<IntegrationStatus[]>('/settings/integrations'),
};
