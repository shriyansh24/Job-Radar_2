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

export interface AnalyticsCompanySizePattern {
  size_bucket: string;
  total_applications: number;
  callbacks: number;
  callback_rate: number;
}

export interface AnalyticsConversionFunnelPattern {
  stage: string;
  count: number;
}

export interface AnalyticsResponseTimePattern {
  avg_days_to_response: number;
  sample_size: number;
  warning: string | null;
}

export interface AnalyticsTimingPattern {
  day_of_week: string;
  total_applications: number;
  callbacks: number;
  callback_rate: number;
}

export interface AnalyticsGhostingPattern {
  company: string;
  total_applications: number;
  ghosted: number;
  ghosting_rate: number;
}

export interface AnalyticsSkillGapPattern {
  skill: string;
  demand_count: number;
}

export interface AnalyticsPatternsResponse {
  callback_rate_by_company_size: AnalyticsCompanySizePattern[];
  conversion_funnel: AnalyticsConversionFunnelPattern[];
  response_time_patterns: AnalyticsResponseTimePattern[];
  best_application_timing: AnalyticsTimingPattern[];
  company_ghosting_rate: AnalyticsGhostingPattern[];
  skill_gap_detection: AnalyticsSkillGapPattern[];
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
  patterns: () =>
    apiClient.get<AnalyticsPatternsResponse>('/analytics/patterns'),
};
