import apiClient from './client';

export interface Application {
  id: string;
  job_id: string | null;
  company_name: string | null;
  position_title: string | null;
  status: string;
  source: string | null;
  applied_at: string | null;
  offer_at: string | null;
  rejected_at: string | null;
  follow_up_at: string | null;
  reminder_at: string | null;
  notes: string | null;
  salary_offered: number | null;
  created_at: string;
  updated_at: string;
}

export interface ApplicationCreate {
  job_id?: string;
  company_name?: string;
  position_title?: string;
  source?: string;
  notes?: string;
  resume_version_id?: string;
}

export interface StatusHistory {
  id: string;
  old_status: string | null;
  new_status: string;
  change_source: string | null;
  note: string | null;
  changed_at: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export const pipelineApi = {
  list: (page?: number, pageSize?: number) =>
    apiClient.get<PaginatedResponse<Application>>('/applications', { params: { page, page_size: pageSize } }),
  pipeline: () =>
    apiClient.get<Record<string, Application[]>>('/applications/pipeline'),
  create: (data: ApplicationCreate) =>
    apiClient.post<Application>('/applications', data),
  update: (id: string, data: Partial<Pick<Application, 'notes' | 'company_name' | 'position_title'>>) =>
    apiClient.patch<Application>(`/applications/${id}`, data),
  transition: (id: string, data: { new_status: string; note?: string }) =>
    apiClient.post<Application>(`/applications/${id}/transition`, data),
  history: (id: string) =>
    apiClient.get<StatusHistory[]>(`/applications/${id}/history`),
};
