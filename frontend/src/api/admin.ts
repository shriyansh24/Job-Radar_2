import apiClient from './client';

export interface HealthStatus {
  status: string;
  database: string;
}

export interface Diagnostics {
  python_version: string;
  platform?: string;
  job_count?: number;
  application_count?: number;
  db_size?: string;
  uptime?: string;
  total_jobs?: number;
  total_users?: number;
  scraper_runs?: number;
}

export interface QueueSnapshot {
  queue_name: string;
  queue_depth: number;
  queue_pressure: string;
  oldest_job_age_seconds: number;
  queue_alert: string;
}

export interface WorkerMetric {
  role: string;
  available: boolean;
  queue_name?: string;
  queue_depth?: number;
  queue_pressure?: string;
  oldest_job_age_seconds?: number;
  queue_alert?: string;
  retry_exhausted_total?: number;
  retry_scheduled_total?: number;
  queue_job_completed_total?: number;
  queue_job_failed_total?: number;
}

export interface RuntimeStatus {
  status: string;
  captured_at: string;
  redis_connected: boolean;
  runtime_error?: string;
  queue_summary: {
    overall_pressure: string;
    overall_alert: string;
    queues: QueueSnapshot[];
  };
  worker_metrics: WorkerMetric[];
  auth_audit_sink: {
    enabled: boolean;
    stream_key: string;
    maxlen: number;
  };
}

export interface SourceHealth {
  id: string;
  source_name: string;
  health_state: string;
  quality_score: number;
  last_check_at: string | null;
  total_jobs_found: number;
  failure_count: number;
  backoff_until: string | null;
  created_at: string;
}

export const adminApi = {
  health: () =>
    apiClient.get<HealthStatus>('/admin/health'),
  diagnostics: () =>
    apiClient.get<Diagnostics>('/admin/diagnostics'),
  runtime: () =>
    apiClient.get<RuntimeStatus>('/admin/runtime'),
  sourceHealth: () =>
    apiClient.get<Array<SourceHealth & { quality_score: number | string }>>('/source-health').then((response) => ({
      ...response,
      data: response.data.map((item) => ({
        ...item,
        quality_score: Number(item.quality_score ?? 0),
      })),
    })),
  reindex: () =>
    apiClient.post('/admin/reindex'),
  exportData: () =>
    apiClient.post('/admin/export', {}, { responseType: 'blob' }),
  importData: (data: Record<string, unknown>) =>
    apiClient.post('/admin/import', data),
  clearData: () =>
    apiClient.delete<{ status: string; rows_deleted: number }>('/admin/data'),
};
