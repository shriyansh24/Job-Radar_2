import apiClient from './client';

export interface ScraperRunResult {
  status?: string;
  message?: string;
  results?: Array<{
    query: string;
    jobs_found?: number;
    jobs_new?: number;
    error?: string;
  }>;
}

export interface TriggerBatchResult {
  run_id: string | null;
  targets_attempted: number;
  targets_succeeded: number;
  targets_failed: number;
  jobs_found: number;
  errors: string[];
}

export interface ScraperRun {
  id: string;
  source: string;
  status: string;
  jobs_found: number;
  jobs_new: number;
  jobs_updated: number;
  error_message: string | null;
  started_at: string;
  completed_at: string | null;
  duration_seconds: number | null;
}

export interface CareerPage {
  id: string;
  url: string;
  company_name: string | null;
  enabled: boolean;
  consecutive_failures: number;
  created_at: string;
  updated_at: string;
}

export interface ScraperEvent {
  type: string;
  data: string;
  timestamp?: string;
}

export interface ScrapeTarget {
  id: string;
  url: string;
  company_name: string | null;
  company_domain: string | null;
  source_kind: string;
  ats_vendor: string | null;
  ats_board_token: string | null;
  start_tier: number;
  max_tier: number;
  priority_class: string;
  schedule_interval_m: number;
  enabled: boolean;
  quarantined: boolean;
  quarantine_reason: string | null;
  last_success_at: string | null;
  last_failure_at: string | null;
  last_success_tier: number | null;
  last_http_status: number | null;
  content_hash: string | null;
  consecutive_failures: number;
  failure_count: number;
  next_scheduled_at: string | null;
  lca_filings: number | null;
  industry: string | null;
  created_at: string;
  updated_at: string;
}

export interface ScrapeAttempt {
  id: string;
  run_id: string | null;
  target_id: string;
  selected_tier: number;
  actual_tier_used: number;
  scraper_name: string;
  parser_name: string | null;
  status: string;
  http_status: number | null;
  duration_ms: number | null;
  retries: number;
  escalations: number;
  jobs_extracted: number;
  content_changed: boolean | null;
  error_class: string | null;
  error_message: string | null;
  browser_used: boolean;
  created_at: string;
}

export interface TargetWithAttempts extends ScrapeTarget {
  recent_attempts: ScrapeAttempt[];
}

interface TargetWithAttemptsApiResponse {
  target: ScrapeTarget;
  recent_attempts: ScrapeAttempt[];
}

export interface ImportResult {
  imported: number;
  skipped: number;
  errors: string[];
}

export interface TargetListParams {
  priority_class?: string;
  ats_vendor?: string;
  quarantined?: boolean;
  enabled?: boolean;
  limit?: number;
  offset?: number;
}

export interface BatchTriggerParams {
  priority_class?: string;
  batch_size?: number;
}

export const scraperApi = {
  stream: () => `/api/v1/scraper/stream`,
  runs: () =>
    apiClient.get<ScraperRun[]>('/scraper/runs'),
  listCareerPages: () =>
    apiClient.get<CareerPage[]>('/scraper/career-pages'),
  createCareerPage: (data: { url: string; company_name?: string }) =>
    apiClient.post<CareerPage>('/scraper/career-pages', data),
  updateCareerPage: (id: string, data: Partial<Pick<CareerPage, 'url' | 'company_name' | 'enabled'>>) =>
    apiClient.patch<CareerPage>(`/scraper/career-pages/${id}`, data),
  deleteCareerPage: (id: string) =>
    apiClient.delete(`/scraper/career-pages/${id}`),
  triggerScraper: () =>
    apiClient.post<ScraperRunResult>('/scraper/run'),
  listTargets: (params?: TargetListParams) =>
    apiClient.get<{ items: ScrapeTarget[]; total: number }>('/scraper/targets', { params }),
  getTarget: (id: string) =>
    apiClient.get<TargetWithAttemptsApiResponse>(`/scraper/targets/${id}`).then((response) => {
      if (!response.data?.target) {
        return { ...response, data: null as unknown as TargetWithAttempts };
      }

      return {
        ...response,
        data: {
          ...response.data.target,
          recent_attempts: response.data.recent_attempts,
        },
      };
    }),
  importTargets: (targets: Partial<ScrapeTarget>[]) =>
    apiClient.post<ImportResult>('/scraper/targets/import', targets),
  triggerTarget: (id: string) =>
    apiClient.post<ScrapeAttempt>(`/scraper/targets/${id}/trigger`),
  updateTarget: (id: string, data: Partial<ScrapeTarget>) =>
    apiClient.patch<ScrapeTarget>(`/scraper/targets/${id}`, data),
  releaseTarget: (id: string, opts?: { force_tier?: number }) =>
    apiClient.post<ScrapeTarget>(`/scraper/targets/${id}/release`, opts),
  listAttempts: (params?: { target_id?: string; run_id?: string; limit?: number }) =>
    apiClient.get<ScrapeAttempt[]>('/scraper/attempts', { params }),
  triggerBatch: (params?: BatchTriggerParams) =>
    apiClient.post<TriggerBatchResult>('/scraper/trigger-batch', params),
};
