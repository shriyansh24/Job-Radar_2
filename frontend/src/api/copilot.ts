import apiClient from './client';

export interface CoverLetterResult {
  id: string;
  job_id: string | null;
  style: string | null;
  content: string;
  created_at: string;
}

export interface CopilotChatResponse {
  response: string;
}

export interface AskHistoryResponse {
  answer: string;
}

export const copilotApi = {
  chat: (message: string, context?: Record<string, unknown> | null, jobId?: string) =>
    apiClient.post<CopilotChatResponse>('/copilot/chat', {
      message,
      context,
      job_id: jobId,
    }),
  askHistory: (question: string) =>
    apiClient.post<AskHistoryResponse>('/copilot/ask-history', { question }),
  generateCoverLetter: (jobId: string, style?: string, template?: string) =>
    apiClient.post<CoverLetterResult>('/copilot/cover-letter', {
      job_id: jobId,
      style,
      template,
    }),
};
