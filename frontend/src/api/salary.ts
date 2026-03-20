import apiClient from './client';

export interface SalaryResearch {
  job_title: string;
  location: string | null;
  min_salary: number | null;
  median_salary: number | null;
  max_salary: number | null;
  percentile_25: number | null;
  percentile_75: number | null;
  data_sources: string[];
  currency: string;
}

export interface OfferEvaluation {
  market_comparison: string;
  percentile: number | null;
  negotiation_tips: string[];
  overall_rating: string;
}

export interface SalaryData {
  min: number;
  percentile_25: number;
  median: number;
  percentile_75: number;
  max: number;
  currency: string;
}

export const salaryApi = {
  research: (data: { job_title: string; company_name?: string; location?: string }) =>
    apiClient.post<SalaryResearch>('/salary/research', data),
  evaluateOffer: (data: { job_title: string; offered_salary: number; company_name?: string; location?: string; offered_benefits?: string[] }) =>
    apiClient.post<OfferEvaluation>('/salary/evaluate-offer', data),
};
