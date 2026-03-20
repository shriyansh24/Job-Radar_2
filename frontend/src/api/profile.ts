import apiClient from './client';

export interface UserProfile {
  full_name: string | null;
  email: string | null;
  phone: string | null;
  location: string | null;
  resume_text: string | null;
  resume_filename: string | null;
  linkedin_url: string | null;
  github_url: string | null;
  portfolio_url: string | null;
  work_authorization: string | null;
  preferred_job_types: string[];
  preferred_remote_types: string[];
  salary_min: number | null;
  salary_max: number | null;
  education: EducationEntry[];
  work_experience: ExperienceEntry[];
  search_queries: string[];
  search_locations: string[];
  watchlist_companies: string[];
  answer_bank: Record<string, string>;
  theme: string;
  notifications_enabled: boolean;
  auto_apply_enabled: boolean;
  created_at: string | null;
  updated_at: string | null;
}

export interface EducationEntry {
  school: string;
  degree: string;
  field: string;
  start_date: string | null;
  end_date: string | null;
}

export interface ExperienceEntry {
  company: string;
  title: string;
  start_date: string | null;
  end_date: string | null;
  description: string | null;
}

export const profileApi = {
  get: () =>
    apiClient.get<UserProfile>('/profile'),
  update: (data: Partial<UserProfile>) =>
    apiClient.patch<UserProfile>('/profile', data),
  generateAnswers: () =>
    apiClient.post('/profile/generate-answers'),
};
