import apiClient from './client';

export interface EmailWebhookPayload {
  sender?: string;
  from_?: string;
  to?: string;
  subject?: string;
  text?: string;
  html?: string;
  timestamp?: string;
  token?: string;
  signature?: string;
}

export interface EmailWebhookResponse {
  status: string;
  action: string | null;
  application_id: string | null;
  company: string | null;
  confidence: number | null;
  message: string | null;
}

export interface EmailLog {
  id: string;
  sender: string;
  subject: string;
  parsed_action: string | null;
  confidence: number | null;
  matched_application_id: string | null;
  company_extracted: string | null;
  job_title_extracted: string | null;
  processed_at: string;
  created_at: string;
}

export const emailApi = {
  listLogs: (limit?: number) =>
    apiClient.get<EmailLog[]>('/email/logs', { params: { limit } }),
  processWebhook: (payload: EmailWebhookPayload) =>
    apiClient.post<EmailWebhookResponse>('/email/webhook', payload),
};
