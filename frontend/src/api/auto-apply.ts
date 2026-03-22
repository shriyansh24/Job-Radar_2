import apiClient from './client';

export interface AutoApplyProfile {
  id: string;
  name: string;
  full_name: string | null;
  email: string | null;
  phone: string | null;
  linkedin_url: string | null;
  github_url: string | null;
  portfolio_url: string | null;
  cover_letter_template: string | null;
  is_active: boolean;
  created_at: string;
}

export interface AutoApplyRule {
  id: string;
  profile_id: string | null;
  name: string | null;
  is_active: boolean;
  priority: number;
  min_match_score: number | null;
  required_keywords: string[];
  excluded_keywords: string[];
  required_companies: string[];
  excluded_companies: string[];
  experience_levels: string[];
  remote_types: string[];
  created_at: string;
}

export interface AutoApplyStats {
  total_runs: number;
  successful: number;
  failed: number;
  pending: number;
}

export interface AutoApplyProfileCreate {
  name: string;
  full_name?: string;
  email?: string;
  phone?: string;
  linkedin_url?: string;
  github_url?: string;
  portfolio_url?: string;
  cover_letter_template?: string;
}

export interface AutoApplyRuleCreate {
  profile_id?: string;
  name?: string;
  is_active?: boolean;
  priority?: number;
  min_match_score?: number;
  required_keywords?: string[];
  excluded_keywords?: string[];
  required_companies?: string[];
  excluded_companies?: string[];
  experience_levels?: string[];
  remote_types?: string[];
}

export interface AutoApplyRun {
  id: string;
  job_id: string;
  rule_id: string | null;
  status: string;
  ats_provider: string | null;
  fields_filled: Record<string, string>;
  fields_missed: string[];
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
}

export const autoApplyApi = {
  listProfiles: () =>
    apiClient.get<AutoApplyProfile[]>('/auto-apply/profiles'),
  createProfile: (data: AutoApplyProfileCreate) =>
    apiClient.post<AutoApplyProfile>('/auto-apply/profiles', data),
  updateProfile: (id: string, data: Partial<AutoApplyProfileCreate>) =>
    apiClient.patch<AutoApplyProfile>(`/auto-apply/profiles/${id}`, data),
  listRules: () =>
    apiClient.get<AutoApplyRule[]>('/auto-apply/rules'),
  createRule: (data: AutoApplyRuleCreate) =>
    apiClient.post<AutoApplyRule>('/auto-apply/rules', data),
  updateRule: (id: string, data: Partial<AutoApplyRuleCreate>) =>
    apiClient.patch<AutoApplyRule>(`/auto-apply/rules/${id}`, data),
  deleteRule: (id: string) =>
    apiClient.delete(`/auto-apply/rules/${id}`),
  getStats: () =>
    apiClient.get<AutoApplyStats>('/auto-apply/stats'),
  run: () =>
    apiClient.post('/auto-apply/run'),
  applySingle: (jobId: string) =>
    apiClient.post('/auto-apply/apply-single', { job_id: jobId }),
  runs: () =>
    apiClient.get<AutoApplyRun[]>('/auto-apply/runs'),
  pause: () =>
    apiClient.post('/auto-apply/pause'),
};
