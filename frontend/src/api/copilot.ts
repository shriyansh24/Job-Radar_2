import apiClient from './client';

export interface CoverLetterResult {
  id: string;
  job_id: string | null;
  style: string | null;
  content: string;
  created_at: string;
}

export const copilotApi = {
  chat: (message: string, jobId?: string) =>
    apiClient.post<{ response: string }>('/copilot/chat', { message, job_id: jobId }),
  generateCoverLetter: (jobId: string, style?: string) =>
    apiClient.post<CoverLetterResult>('/copilot/cover-letter', { job_id: jobId, style }),
};
