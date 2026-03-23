import apiClient from './client';

export interface Job {
  id: string;
  source: string;
  source_url: string | null;
  title: string;
  company_name: string | null;
  company_domain: string | null;
  company_logo_url: string | null;
  location: string | null;
  location_city: string | null;
  location_state: string | null;
  location_country: string | null;
  remote_type: string | null;
  description_markdown: string | null;
  summary_ai: string | null;
  skills_required: string[];
  skills_nice_to_have: string[];
  tech_stack: string[];
  red_flags: string[];
  green_flags: string[];
  match_score: number | null;
  tfidf_score: number | null;
  freshness_score: number | null;
  salary_min: number | null;
  salary_max: number | null;
  salary_period: string | null;
  salary_currency: string;
  experience_level: string | null;
  job_type: string | null;
  status: string;
  is_starred: boolean;
  is_enriched: boolean;
  is_hidden: boolean;
  posted_at: string | null;
  scraped_at: string;
  created_at: string;
}

export interface JobListParams {
  q?: string;
  source?: string;
  remote_type?: string;
  experience_level?: string;
  job_type?: string;
  min_match_score?: number;
  status?: string;
  is_starred?: boolean;
  sort_by?: string;
  sort_order?: string;
  page?: number;
  page_size?: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export const jobsApi = {
  list: (params: JobListParams) =>
    apiClient.get<PaginatedResponse<Job>>('/jobs', { params }),
  get: (id: string) =>
    apiClient.get<Job>(`/jobs/${id}`),
  update: (id: string, data: Partial<Pick<Job, 'is_starred' | 'status'>>) =>
    apiClient.patch<Job>(`/jobs/${id}`, data),
  delete: (id: string) =>
    apiClient.delete(`/jobs/${id}`),
  semanticSearch: (query: string, limit?: number) =>
    apiClient.post<Job[]>('/jobs/search/semantic', { query, limit }),
  export: (format: string, filters?: JobListParams) =>
    apiClient.post('/jobs/export', { format, filters }, { responseType: 'blob' }),
};
