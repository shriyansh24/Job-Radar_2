import apiClient from './client';

export interface ResumeVersion {
  id: string;
  label: string | null;
  filename: string | null;
  parsed_text: string | null;
  parsed_structured: Record<string, unknown> | null;
  is_default: boolean;
  created_at: string;
}

export interface ResumeTemplate {
  id: string;
  name: string;
  description: string;
}

export interface ResumePreview {
  template_id: string;
  html: string;
}

export interface ResumeTailorStage1 {
  hard_requirements: string[];
  soft_requirements: string[];
  key_technologies: string[];
  ats_keywords: string[];
  culture_signals: string[];
  seniority_indicators: string[];
  deal_breakers: string[];
}

export interface ResumeTailorPartialMatch {
  requirement: string;
  evidence: string;
  gap: string;
}

export interface ResumeTailorStage2 {
  matched_requirements: string[];
  partial_matches: ResumeTailorPartialMatch[];
  missing_requirements: string[];
  transferable_skills: string[];
  keyword_coverage: {
    present: string[];
    missing: string[];
  };
  strength_areas: string[];
  risk_areas: string[];
}

export interface ResumeTailorResponse {
  summary: string;
  reordered_experience: Array<{
    company: string;
    bullets: string[];
  }>;
  enhanced_bullets: Array<{
    original: string;
    enhanced: string;
  }>;
  skills_section: string[];
  ats_score_before: number;
  ats_score_after: number;
  stage1_output: ResumeTailorStage1 | null;
  stage2_output: ResumeTailorStage2 | null;
}

export interface CouncilEvaluation {
  evaluations: { model: string; score: number; feedback: string; strengths: string[]; weaknesses: string[] }[];
  overall_score: number | null;
  consensus: string | null;
}

export const resumeApi = {
  listVersions: () =>
    apiClient.get<ResumeVersion[]>('/resume/versions'),
  listTemplates: () =>
    apiClient.get<ResumeTemplate[]>('/resume/templates'),
  getVersion: (id: string) =>
    apiClient.get<ResumeVersion>(`/resume/versions/${id}`),
  preview: (resumeVersionId: string, templateId: string) =>
    apiClient.get<ResumePreview>(`/resume/versions/${resumeVersionId}/preview`, {
      params: { template_id: templateId },
    }),
  exportVersion: (resumeVersionId: string, templateId: string) =>
    apiClient.get<Blob>(`/resume/versions/${resumeVersionId}/export`, {
      params: { template_id: templateId },
      responseType: 'blob',
    }),
  upload: (file: File) => {
    const form = new FormData();
    form.append('file', file);
    return apiClient.post<ResumeVersion>('/resume/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  tailor: (resumeVersionId: string, jobId: string) =>
    apiClient.post<ResumeTailorResponse>('/resume/tailor', { resume_version_id: resumeVersionId, job_id: jobId }),
  council: (resumeVersionId: string, jobId?: string) =>
    apiClient.post<CouncilEvaluation>('/resume/council', { resume_version_id: resumeVersionId, job_id: jobId }),
};
