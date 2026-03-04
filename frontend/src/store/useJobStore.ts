import { create } from 'zustand'
import type { Job, JobFilters } from '../api/client'

interface ScraperLog {
  timestamp: string
  source: string
  message: string
  type: 'info' | 'success' | 'error'
}

interface JobStore {
  // Selected job
  selectedJobId: string | null
  setSelectedJobId: (id: string | null) => void

  // Filters
  filters: JobFilters
  setFilters: (filters: Partial<JobFilters>) => void
  resetFilters: () => void

  // View mode
  viewMode: 'list' | 'grid'
  setViewMode: (mode: 'list' | 'grid') => void

  // Scraper state
  isScraperRunning: boolean
  setIsScraperRunning: (running: boolean) => void
  scraperLogs: ScraperLog[]
  addScraperLog: (log: ScraperLog) => void
  clearScraperLogs: () => void

  // Scraper log drawer
  isLogDrawerOpen: boolean
  setIsLogDrawerOpen: (open: boolean) => void

  // Filter panel
  isFilterPanelOpen: boolean
  setIsFilterPanelOpen: (open: boolean) => void

  // Total job count (live from SSE)
  totalJobCount: number
  setTotalJobCount: (count: number) => void

  // Resume active
  isResumeActive: boolean
  setIsResumeActive: (active: boolean) => void
}

const DEFAULT_FILTERS: JobFilters = {
  page: 1,
  limit: 50,
  sort_by: 'scraped_at',
  sort_dir: 'desc',
}

export const useJobStore = create<JobStore>((set) => ({
  selectedJobId: null,
  setSelectedJobId: (id) => set({ selectedJobId: id }),

  filters: { ...DEFAULT_FILTERS },
  setFilters: (filters) =>
    set((state) => ({ filters: { ...state.filters, ...filters, page: filters.page ?? 1 } })),
  resetFilters: () => set({ filters: { ...DEFAULT_FILTERS } }),

  viewMode: 'list',
  setViewMode: (mode) => set({ viewMode: mode }),

  isScraperRunning: false,
  setIsScraperRunning: (running) => set({ isScraperRunning: running }),
  scraperLogs: [],
  addScraperLog: (log) =>
    set((state) => ({
      scraperLogs: [...state.scraperLogs.slice(-200), log],
    })),
  clearScraperLogs: () => set({ scraperLogs: [] }),

  isLogDrawerOpen: false,
  setIsLogDrawerOpen: (open) => set({ isLogDrawerOpen: open }),

  isFilterPanelOpen: true,
  setIsFilterPanelOpen: (open) => set({ isFilterPanelOpen: open }),

  totalJobCount: 0,
  setTotalJobCount: (count) => set({ totalJobCount: count }),

  isResumeActive: false,
  setIsResumeActive: (active) => set({ isResumeActive: active }),
}))
