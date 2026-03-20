import apiClient from './client';

export interface ScraperRunResult {
  run_id: string;
  jobs_found: number;
  jobs_new: number;
  jobs_updated: number;
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
  use_spider: boolean;
  consecutive_failures: number;
  last_scraped_at: string | null;
  last_error: string | null;
  created_at: string;
}

export interface ScraperEvent {
  type: string;
  data: string;
  timestamp?: string;
}

export const scraperApi = {
  stream: () => `/api/v1/scraper/stream`,
  runs: () =>
    apiClient.get<ScraperRun[]>('/scraper/runs'),
  listCareerPages: () =>
    apiClient.get<CareerPage[]>('/scraper/career-pages'),
  createCareerPage: (data: { url: string; company_name?: string }) =>
    apiClient.post<CareerPage>('/scraper/career-pages', data),
  updateCareerPage: (id: string, data: Partial<Pick<CareerPage, 'url' | 'company_name' | 'enabled' | 'use_spider'>>) =>
    apiClient.patch<CareerPage>(`/scraper/career-pages/${id}`, data),
  deleteCareerPage: (id: string) =>
    apiClient.delete(`/scraper/career-pages/${id}`),
};
