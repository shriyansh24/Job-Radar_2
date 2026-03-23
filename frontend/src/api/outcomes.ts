import apiClient from './client';

export interface Outcome {
  id: string;
  application_id: string;
  user_id: string;
  stage_reached: string | null;
  rejection_reason: string | null;
  rejection_stage: string | null;
  days_to_response: number | null;
  offer_amount: number | null;
  offer_equity: string | null;
  offer_total_comp: number | null;
  negotiated_amount: number | null;
  final_decision: string | null;
  was_ghosted: boolean;
  referral_used: boolean;
  cover_letter_used: boolean;
  application_method: string | null;
  feedback_notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface OutcomeMutation {
  rejection_reason?: string | null;
  rejection_stage?: string | null;
  days_to_response?: number | null;
  offer_amount?: number | null;
  offer_equity?: string | null;
  offer_total_comp?: number | null;
  negotiated_amount?: number | null;
  final_decision?: string | null;
  was_ghosted?: boolean;
  referral_used?: boolean;
  cover_letter_used?: boolean;
  application_method?: string | null;
  feedback_notes?: string | null;
  stage_reached?: string | null;
}

export interface RejectionReasonCount {
  reason: string;
  count: number;
}

export interface UserOutcomeStats {
  total_applications: number;
  total_outcomes: number;
  avg_days_to_response: number | null;
  ghosting_rate: number;
  response_rate: number;
  offer_rate: number;
  avg_offer_amount: number | null;
  top_rejection_reasons: RejectionReasonCount[];
  stage_distribution: Record<string, number>;
}

export interface CompanyInsight {
  id: string;
  company_name: string;
  total_applications: number;
  callback_count: number;
  avg_response_days: number | null;
  ghosted_count: number;
  ghost_rate: number;
  rejection_rate: number;
  offer_rate: number;
  offers_received: number;
  avg_offer_amount: number | null;
  interview_difficulty: number | null;
  culture_notes: string | null;
  last_applied_at: string | null;
}

export const outcomesApi = {
  create: (applicationId: string, data: OutcomeMutation) =>
    apiClient.post<Outcome>(`/outcomes/${applicationId}`, data),
  update: (applicationId: string, data: OutcomeMutation) =>
    apiClient.patch<Outcome>(`/outcomes/${applicationId}`, data),
  get: (applicationId: string) =>
    apiClient.get<Outcome>(`/outcomes/${applicationId}`),
  getStats: () =>
    apiClient.get<UserOutcomeStats>('/outcomes/stats/me'),
  getCompanyInsights: (company: string) =>
    apiClient.get<CompanyInsight>(`/outcomes/companies/${encodeURIComponent(company)}/insights`),
};
