import apiClient from './client';

export interface InterviewSession {
  id: string;
  job_id: string | null;
  questions: InterviewQuestion[];
  answers: Record<string, unknown>[];
  scores: InterviewScore[];
  overall_score: number | null;
  created_at: string;
}

export interface InterviewQuestion {
  question: string;
  category?: string | null;
  type?: string | null;
  difficulty?: string | null;
}

export interface InterviewScore {
  question_index?: number;
  score?: number | null;
}

export interface GenerateParams {
  job_id: string;
  count?: number;
  types?: string[];
}

export interface EvaluateParams {
  session_id: string;
  question_index: number;
  answer: string;
}

export interface EvaluateResult {
  score: number;
  feedback: string;
  strengths: string[];
  improvements: string[];
}

// -- Contextual Prep types --

export type PrepStage = 'phone_screen' | 'technical' | 'behavioral' | 'final' | 'general';

export interface CompanyResearch {
  overview: string;
  recent_news: string[];
  culture_values: string[];
  interview_style: string;
}

export interface RoleAnalysis {
  key_requirements: string[];
  skill_gaps: string[];
  talking_points: string[];
  seniority_expectations: string;
}

export interface PrepQuestion {
  question: string;
  category: string;
  why_likely: string;
  suggested_approach: string;
}

export interface StarResponse {
  situation: string;
  task: string;
  action: string;
  result: string;
}

export interface SuggestedAnswer {
  question: string;
  star_response: StarResponse;
  key_points: string[];
}

export interface QuestionToAsk {
  question: string;
  why_effective: string;
  what_to_listen_for: string;
}

export interface PrepRedFlag {
  trap: string;
  why_dangerous: string;
  better_approach: string;
}

export interface ContextualPrepData {
  company_research: CompanyResearch;
  role_analysis: RoleAnalysis;
  likely_questions: PrepQuestion[];
  suggested_answers: SuggestedAnswer[];
  questions_to_ask: QuestionToAsk[];
  red_flags: PrepRedFlag[];
}

export interface ContextualPrepResponse {
  id: string;
  application_id: string;
  stage: string;
  prep_data: ContextualPrepData;
  created_at: string;
  updated_at: string;
}

export const interviewApi = {
  listSessions: () =>
    apiClient.get<InterviewSession[]>('/interview/sessions'),
  getSession: (id: string) =>
    apiClient.get<InterviewSession>(`/interview/sessions/${id}`),
  generate: (data: GenerateParams) =>
    apiClient.post<InterviewSession>('/interview/generate', data),
  evaluate: (data: EvaluateParams) =>
    apiClient.post<EvaluateResult>('/interview/evaluate', data),
  // Contextual prep
  generatePrep: (applicationId: string, stage: PrepStage = 'general') =>
    apiClient.post<ContextualPrepResponse>(`/interview/prep/${applicationId}`, { stage }),
  getPrep: (applicationId: string) =>
    apiClient.get<ContextualPrepResponse>(`/interview/prep/${applicationId}`),
};
