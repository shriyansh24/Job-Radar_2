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

export interface InterviewLikelyQuestion {
  question: string;
  category: string;
}

export interface InterviewStarStory {
  situation: string;
  task: string;
  action: string;
  result: string;
}

export interface InterviewRedFlagResponse {
  question: string;
  avoid: string;
  instead: string;
}

export interface InterviewPrepRequest {
  job_id: string;
  resume_text: string;
  stage?: string;
  job_title?: string;
  company_name?: string;
  job_description?: string;
  required_skills?: string[];
}

export interface InterviewCompanyResearch {
  overview: string;
  recent_news: string[];
  culture_values: string[];
  interview_style: string;
}

export interface InterviewRoleAnalysis {
  key_requirements: string[];
  skill_gaps: string[];
  talking_points: string[];
  seniority_expectations: string;
}

export interface InterviewPrepBundle {
  likely_questions: InterviewLikelyQuestion[];
  star_stories: InterviewStarStory[];
  technical_topics: string[];
  company_talking_points: string[];
  questions_to_ask: string[];
  red_flag_responses: InterviewRedFlagResponse[];
  company_research?: InterviewCompanyResearch | null;
  role_analysis?: InterviewRoleAnalysis | null;
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
  prepare: (data: InterviewPrepRequest) =>
    apiClient.post<InterviewPrepBundle>('/interview/prepare', data),
  evaluate: (data: EvaluateParams) =>
    apiClient.post<EvaluateResult>('/interview/evaluate', data),
};
