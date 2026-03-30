import apiClient from './client';

type NumberLike = number | string | null | undefined;

function toNumber(value: NumberLike): number | null {
  if (value === null || value === undefined || value === '') {
    return null;
  }

  const normalized = typeof value === 'number' ? value : Number(value);
  return Number.isFinite(normalized) ? normalized : null;
}

export interface SalaryResearch {
  job_title: string;
  location: string | null;
  p25: number | null;
  p50: number | null;
  p75: number | null;
  p90: number | null;
  yoe_brackets: Array<{ years: string; range: string }>;
  competing_companies: string[];
  currency: string;
  cached: boolean;
}

export interface OfferEvaluation {
  assessment: string;
  counter_offer: number | null;
  walkaway_point: number | null;
  talking_points: string[];
  negotiation_script: string;
}

export const salaryApi = {
  research: (data: { job_title: string; company_name?: string; location?: string }) =>
    apiClient.post<SalaryResearch>('/salary/research', data).then((response) => ({
      ...response,
      data: {
        ...response.data,
        p25: toNumber(response.data.p25),
        p50: toNumber(response.data.p50),
        p75: toNumber(response.data.p75),
        p90: toNumber(response.data.p90),
      },
    })),
  evaluateOffer: (data: { job_title: string; offered_salary: number; company_name?: string; location?: string; offered_benefits?: string[] }) =>
    apiClient.post<OfferEvaluation>('/salary/evaluate-offer', data).then((response) => ({
      ...response,
      data: {
        ...response.data,
        counter_offer: toNumber(response.data.counter_offer),
        walkaway_point: toNumber(response.data.walkaway_point),
      },
    })),
};
