import apiClient from './client';

export interface HealthStatus {
  status: string;
  database: string;
}

export interface Diagnostics {
  python_version: string;
  db_size: string;
  uptime: string;
  total_jobs: number;
  total_users: number;
  scraper_runs: number;
}

export interface SourceHealth {
  id: string;
  source_name: string;
  health_state: string;
  last_check_at: string | null;
  total_jobs_found: number;
  failure_count: number;
  recent_checks: SourceCheck[];
}

export interface SourceCheck {
  id: string;
  status: string;
  jobs_found: number;
  error_message: string | null;
  checked_at: string;
}

export const adminApi = {
  health: () =>
    apiClient.get<HealthStatus>('/admin/health'),
  diagnostics: () =>
    apiClient.get<Diagnostics>('/admin/diagnostics'),
  sourceHealth: () =>
    apiClient.get<SourceHealth[]>('/source-health'),
  reindex: () =>
    apiClient.post('/admin/reindex'),
  exportData: () =>
    apiClient.post('/admin/export', {}, { responseType: 'blob' }),
  importData: (data: Record<string, unknown>) =>
    apiClient.post('/admin/import', data),
  clearData: () =>
    apiClient.delete<{ status: string; rows_deleted: number }>('/admin/data'),
};
