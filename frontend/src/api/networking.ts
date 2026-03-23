import apiClient from './client';

export interface Contact {
  id: string;
  name: string;
  company: string | null;
  role: string | null;
  relationship_strength: number;
  linkedin_url: string | null;
  email: string | null;
  last_contacted: string | null;
  notes: string | null;
  created_at: string | null;
}

export interface ContactCreate {
  name: string;
  company?: string | null;
  role?: string | null;
  relationship_strength?: number;
  linkedin_url?: string | null;
  email?: string | null;
  notes?: string | null;
}

export interface ContactUpdate {
  name?: string;
  company?: string | null;
  role?: string | null;
  relationship_strength?: number;
  linkedin_url?: string | null;
  email?: string | null;
  notes?: string | null;
}

export interface ReferralSuggestion {
  contact: Contact;
  relevance_reason: string;
  suggested_message: string;
}

export interface ReferralRequest {
  id: string;
  contact_id: string;
  job_id: string;
  status: string;
  message_template: string | null;
  sent_at: string | null;
  created_at: string | null;
}

export interface ReferralRequestCreate {
  contact_id: string;
  job_id: string;
  message_template?: string | null;
}

export const networkingApi = {
  createContact: (data: ContactCreate) =>
    apiClient.post<Contact>('/networking/contacts', data),
  listContacts: () =>
    apiClient.get<Contact[]>('/networking/contacts'),
  getContact: (contactId: string) =>
    apiClient.get<Contact>(`/networking/contacts/${contactId}`),
  updateContact: (contactId: string, data: ContactUpdate) =>
    apiClient.patch<Contact>(`/networking/contacts/${contactId}`, data),
  deleteContact: (contactId: string) =>
    apiClient.delete(`/networking/contacts/${contactId}`),
  findConnections: (company: string) =>
    apiClient.get<Contact[]>(`/networking/connections/${encodeURIComponent(company)}`),
  suggestReferrals: (jobId: string) =>
    apiClient.get<ReferralSuggestion[]>(`/networking/referral-suggestions/${jobId}`),
  generateOutreach: (contactId: string, jobId: string) =>
    apiClient.post<{ message: string }>('/networking/outreach', {
      contact_id: contactId,
      job_id: jobId,
    }),
  createReferralRequest: (data: ReferralRequestCreate) =>
    apiClient.post<ReferralRequest>('/networking/referral-requests', data),
  listReferralRequests: () =>
    apiClient.get<ReferralRequest[]>('/networking/referral-requests'),
};
