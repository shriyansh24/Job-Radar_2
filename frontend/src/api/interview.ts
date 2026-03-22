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

export const interviewApi = {
  listSessions: () =>
    apiClient.get<InterviewSession[]>('/interview/sessions'),
  getSession: (id: string) =>
    apiClient.get<InterviewSession>(`/interview/sessions/${id}`),
  generate: (data: GenerateParams) =>
    apiClient.post<InterviewSession>('/interview/generate', data),
  evaluate: (data: EvaluateParams) =>
    apiClient.post<EvaluateResult>('/interview/evaluate', data),
};
