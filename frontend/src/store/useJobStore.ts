import { create } from 'zustand';

export interface JobListParams {
  q?: string;
  source?: string;
  remote_type?: string;
  experience_level?: string;
  min_match_score?: number;
  status?: string;
  is_starred?: boolean;
  sort_by?: string;
  sort_order?: string;
  page?: number;
  page_size?: number;
}

interface JobState {
  selectedJobId: string | null;
  filters: JobListParams;
  setSelectedJob: (id: string | null) => void;
  setFilters: (filters: Partial<JobListParams>) => void;
  resetFilters: () => void;
}

const defaultFilters: JobListParams = {
  page: 1,
  page_size: 20,
  sort_by: 'scraped_at',
  sort_order: 'desc',
};

export const useJobStore = create<JobState>((set) => ({
  selectedJobId: null,
  filters: { ...defaultFilters },
  setSelectedJob: (id) => set({ selectedJobId: id }),
  setFilters: (filters) =>
    set((state) => ({
      filters: { ...state.filters, ...filters, page: filters.page ?? 1 },
    })),
  resetFilters: () => set({ filters: { ...defaultFilters }, selectedJobId: null }),
}));
