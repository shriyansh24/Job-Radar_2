import apiClient from './client';

export interface AnalyticsOverview {
  total_jobs: number;
  total_applications: number;
  total_interviews: number;
  total_offers: number;
  applications_by_status: Record<string, number>;
  response_rate: number;
  avg_days_to_response: number;
  jobs_scraped_today: number;
  enriched_jobs: number;
}

export type OverviewStats = AnalyticsOverview;

export interface DailyStats {
  date: string;
  jobs_scraped: number;
  applications: number;
}

export interface SourceStats {
  source: string;
  total_jobs: number;
  quality_score: number;
  avg_match_score: number | null;
}

export interface SkillStats {
  skill: string;
  count: number;
  percentage: number;
}

export interface FunnelData {
  stage: string;
  count: number;
}

export const analyticsApi = {
  overview: () =>
    apiClient.get<AnalyticsOverview>('/analytics/overview'),
  daily: (days?: number) =>
    apiClient.get<DailyStats[]>('/analytics/daily', { params: { days } }),
  sources: () =>
    apiClient.get<SourceStats[]>('/analytics/sources'),
  skills: (limit?: number) =>
    apiClient.get<SkillStats[]>('/analytics/skills', { params: { limit } }),
  funnel: () =>
    apiClient.get<FunnelData[]>('/analytics/funnel'),
};
