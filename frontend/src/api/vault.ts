import apiClient from './client';
import type { ResumeVersion } from './resume';
import type { CoverLetterResult } from './copilot';

export const vaultApi = {
  listResumes: () =>
    apiClient.get<ResumeVersion[]>('/vault/resumes'),
  listCoverLetters: () =>
    apiClient.get<CoverLetterResult[]>('/vault/cover-letters'),
  deleteResume: (id: string) =>
    apiClient.delete(`/vault/resumes/${id}`),
  deleteCoverLetter: (id: string) =>
    apiClient.delete(`/vault/cover-letters/${id}`),
};
