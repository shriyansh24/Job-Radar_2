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

export interface TailorResult {
  tailored_text: string;
  suggestions: string[];
  sections_modified: string[];
}

export interface CouncilEvaluation {
  evaluations: { model: string; score: number; feedback: string; strengths: string[]; weaknesses: string[] }[];
  overall_score: number | null;
  consensus: string | null;
}

export const resumeApi = {
  listVersions: () =>
    apiClient.get<ResumeVersion[]>('/resume/versions'),
  getVersion: (id: string) =>
    apiClient.get<ResumeVersion>(`/resume/versions/${id}`),
  upload: (file: File) => {
    const form = new FormData();
    form.append('file', file);
    return apiClient.post<ResumeVersion>('/resume/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  tailor: (resumeVersionId: string, jobId: string) =>
    apiClient.post<TailorResult>('/resume/tailor', { resume_version_id: resumeVersionId, job_id: jobId }),
  council: (resumeVersionId: string, jobId?: string) =>
    apiClient.post<CouncilEvaluation>('/resume/council', { resume_version_id: resumeVersionId, job_id: jobId }),
};
