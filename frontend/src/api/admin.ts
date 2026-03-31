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

export interface QueueAlertRouting {
  stream_key: string;
  stream_maxlen: number;
  webhook_enabled: boolean;
  webhook_host: string | null;
}

export interface QueueTelemetrySample {
  stream_id: string;
  captured_at: string;
  overall_pressure: string;
  overall_alert: string;
  queues: QueueSnapshot[];
}

export interface QueueAlertEvent {
  stream_id: string;
  captured_at: string;
  scope: "overall" | "queue";
  queue_name: string;
  previous_pressure: string;
  current_pressure: string;
  previous_alert: string;
  current_alert: string;
  queue_depth: number;
  oldest_job_age_seconds: number;
}

export interface AuthAuditEvent {
  stream_id: string;
  event: string;
  audit_stream: string;
  timestamp: string;
  request_id?: string;
  user_id?: string;
  reason?: string;
  auth_source?: string;
  token_version?: string;
  cleared_cookie_names?: string;
  queue_name?: string;
  role?: string;
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
  queue_alert_routing: QueueAlertRouting;
  recent_queue_samples: QueueTelemetrySample[];
  recent_queue_alerts: QueueAlertEvent[];
  recent_auth_audit_events: AuthAuditEvent[];
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
