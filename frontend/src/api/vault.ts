import apiClient from './client';
import type { ResumeVersion } from './resume';
import type { CoverLetterResult } from './copilot';

export const vaultApi = {
  listResumes: () =>
    apiClient.get<ResumeVersion[]>('/vault/resumes'),
  listCoverLetters: () =>
    apiClient.get<CoverLetterResult[]>('/vault/cover-letters'),
  updateResume: (id: string, label: string) =>
    apiClient.patch<ResumeVersion>(`/vault/resumes/${id}`, null, {
      params: { label },
    }),
  updateCoverLetter: (id: string, content: string) =>
    apiClient.patch<CoverLetterResult>(`/vault/cover-letters/${id}`, null, {
      params: { content },
    }),
  deleteResume: (id: string) =>
    apiClient.delete(`/vault/resumes/${id}`),
  deleteCoverLetter: (id: string) =>
    apiClient.delete(`/vault/cover-letters/${id}`),
};
