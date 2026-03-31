import apiClient from './client';
import { API_BASE_URL } from '../lib/constants';

export interface SavedSearch {
  id: string;
  name: string;
  filters: Record<string, unknown>;
  alert_enabled: boolean;
  last_checked_at: string | null;
  last_matched_at: string | null;
  last_match_count: number;
  last_error: string | null;
  created_at: string;
}

export interface SavedSearchCheckResult {
  search: SavedSearch;
  status: "matched" | "no_match";
  new_matches: number;
  notification_created: boolean;
  notification_id: string | null;
  link: string;
}

export interface AppSettings {
  theme: string;
  notifications_enabled: boolean;
  auto_apply_enabled: boolean;
}

export type IntegrationProvider = 'openrouter' | 'serpapi' | 'theirstack' | 'apify' | 'google';
export type IntegrationAuthType = 'api_key' | 'oauth';
export type IntegrationConnectionStatus = 'connected' | 'not_configured' | 'needs_reconnect' | 'sync_error';

export interface IntegrationStatus {
  provider: IntegrationProvider;
  auth_type: IntegrationAuthType;
  connected: boolean;
  status: IntegrationConnectionStatus;
  masked_value: string | null;
  account_email: string | null;
  scopes: string[];
  updated_at: string | null;
  last_validated_at: string | null;
  last_synced_at: string | null;
  last_error: string | null;
}

export interface GmailSyncResult {
  provider: 'google';
  messages_seen: number;
  messages_processed: number;
  messages_failed: number;
  duplicates_skipped: number;
  signals_detected: number;
  transitions_applied: number;
  last_synced_at: string | null;
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
  checkSearch: (id: string) =>
    apiClient.post<SavedSearchCheckResult>(`/settings/searches/${id}/check`),
  deleteSearch: (id: string) =>
    apiClient.delete(`/settings/searches/${id}`),
  listIntegrations: () =>
    apiClient.get<IntegrationStatus[]>('/settings/integrations'),
  upsertIntegration: (
    provider: Exclude<IntegrationProvider, 'google'>,
    apiKey: string
  ) => apiClient.put<IntegrationStatus>(`/settings/integrations/${provider}`, { api_key: apiKey }),
  deleteIntegration: (provider: IntegrationProvider) =>
    apiClient.delete(`/settings/integrations/${provider}`),
  buildGoogleConnectUrl: (returnTo = "/settings?tab=integrations") =>
    `${API_BASE_URL}/settings/integrations/google/connect?return_to=${encodeURIComponent(returnTo)}`,
  syncGoogleIntegration: () =>
    apiClient.post<GmailSyncResult>('/settings/integrations/google/sync'),
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
  checkSavedSearch: (id: string) =>
    apiClient.post<SavedSearchCheckResult>(`/settings/searches/${id}/check`),
  deleteSavedSearch: (id: string) =>
    apiClient.delete(`/settings/searches/${id}`),
  integrations: () =>
    apiClient.get<IntegrationStatus[]>('/settings/integrations'),
};
