import apiClient from "./client";

// -- Canonical Jobs --

export interface CanonicalJob {
  id: string;
  title: string;
  company_name: string;
  company_domain: string | null;
  location: string | null;
  remote_type: string | null;
  status: string;
  source_count: number;
  first_seen_at: string;
  last_refreshed_at: string;
  is_stale: boolean;
  merged_data: Record<string, unknown> | null;
  created_at: string;
}

export interface RawJobSource {
  id: string;
  source: string;
  source_url: string | null;
  job_id: string | null;
  scraped_at: string | null;
}

export interface CanonicalJobDetail extends CanonicalJob {
  sources: RawJobSource[];
}

export const canonicalJobsApi = {
  list: (params?: { status?: string; stale_only?: boolean; limit?: number }) =>
    apiClient
      .get<CanonicalJob[]>("/canonical-jobs", { params })
      .then((r) => r.data),

  listStale: (limit = 50) =>
    apiClient
      .get<CanonicalJob[]>("/canonical-jobs/stale", { params: { limit } })
      .then((r) => r.data),

  get: (id: string) =>
    apiClient
      .get<CanonicalJobDetail>(`/canonical-jobs/${id}`)
      .then((r) => r.data),

  close: (id: string) =>
    apiClient.post<CanonicalJob>(`/canonical-jobs/${id}/close`).then((r) => r.data),

  reactivate: (id: string) =>
    apiClient
      .post<CanonicalJob>(`/canonical-jobs/${id}/reactivate`)
      .then((r) => r.data),
};

// -- Companies --

export interface Company {
  id: string;
  canonical_name: string;
  domain: string | null;
  careers_url: string | null;
  ats_provider: string | null;
  validation_state: string;
  confidence_score: number;
  job_count: number;
  source_count: number;
  ats_slug: string | null;
  last_validated_at: string | null;
}

export const companiesApi = {
  list: (params?: { validation_state?: string }) =>
    apiClient.get<Company[]>("/companies", { params }).then((r) => r.data),

  get: (domain: string) =>
    apiClient.get<Company>(`/companies/${domain}`).then((r) => r.data),
};

// -- Source Health --

export interface SourceHealth {
  id: string;
  source_name: string;
  health_state: string;
  quality_score: number;
  total_jobs_found: number;
  last_check_at: string | null;
  failure_count: number;
  source_type: string | null;
}

export const sourceHealthApi = {
  list: () =>
    apiClient.get<SourceHealth[]>("/source-health").then((r) => r.data),
};

// -- Search Expansion --

export interface QueryTemplate {
  id: string;
  name: string;
  base_query: string;
  expanded_queries: string[] | null;
  strictness: string;
  is_active: boolean;
  created_at: string;
}

export const searchExpansionApi = {
  listTemplates: () =>
    apiClient.get<QueryTemplate[]>("/search-expansion").then((r) => r.data),
};
