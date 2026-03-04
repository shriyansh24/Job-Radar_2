import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
})

// --- Jobs ---
export interface Job {
  job_id: string
  source: string
  url: string
  posted_at: string | null
  scraped_at: string
  is_active: boolean
  duplicate_of: string | null
  company_name: string
  company_domain: string | null
  company_logo_url: string | null
  title: string
  location_city: string | null
  location_state: string | null
  location_country: string | null
  remote_type: string | null
  job_type: string | null
  experience_level: string | null
  department: string | null
  industry: string | null
  salary_min: number | null
  salary_max: number | null
  salary_currency: string | null
  salary_period: string | null
  description_raw: string | null
  description_clean: string | null
  description_markdown: string | null
  skills_required: string[] | null
  skills_nice_to_have: string[] | null
  tech_stack: string[] | null
  seniority_score: number | null
  remote_score: number | null
  match_score: number | null
  summary_ai: string | null
  red_flags: string[] | null
  green_flags: string[] | null
  is_enriched: boolean
  enriched_at: string | null
  status: string
  notes: string | null
  applied_at: string | null
  last_updated: string | null
  is_starred: boolean
  tags: string[] | null
}

export interface JobListResponse {
  jobs: Job[]
  total: number
  page: number
  limit: number
  has_more: boolean
}

export interface JobFilters {
  page?: number
  limit?: number
  q?: string
  location?: string
  source?: string
  status?: string
  experience_level?: string
  remote_type?: string
  posted_within_days?: number
  min_match_score?: number
  min_salary?: number
  tech_stack?: string
  company?: string
  is_starred?: boolean
  sort_by?: string
  sort_dir?: string
}

export const fetchJobs = (filters: JobFilters = {}) =>
  api.get<JobListResponse>('/jobs', { params: filters }).then((r) => r.data)

export const fetchJob = (id: string) =>
  api.get<Job>(`/jobs/${id}`).then((r) => r.data)

export const updateJob = (id: string, data: Partial<Job>) =>
  api.patch<Job>(`/jobs/${id}`, data).then((r) => r.data)

// --- Stats ---
export interface Stats {
  total_jobs: number
  new_today: number
  by_source: Record<string, number>
  by_status: Record<string, number>
  by_experience_level: Record<string, number>
  top_companies: { name: string; count: number }[]
  top_skills: { skill: string; count: number }[]
  jobs_over_time: Record<string, any>[]
  avg_match_score: number | null
}

export const fetchStats = () => api.get<Stats>('/stats').then((r) => r.data)

// --- Scraper ---
export interface ScraperRun {
  id: number
  source: string
  started_at: string
  completed_at: string | null
  jobs_found: number
  jobs_new: number
  jobs_updated: number
  error_message: string | null
  status: string
}

export const triggerScraper = (source: string) =>
  api.post<ScraperRun[]>('/scraper/run', { source }).then((r) => r.data)

export const fetchScraperStatus = () =>
  api.get<{ runs: ScraperRun[]; is_running: boolean }>('/scraper/status').then((r) => r.data)

// --- Search ---
export const semanticSearch = (q: string, limit = 20) =>
  api.get('/search/semantic', { params: { q, limit } }).then((r) => r.data)

// --- Settings ---
export interface Settings {
  serpapi_key_set: boolean
  theirstack_key_set: boolean
  apify_key_set: boolean
  openrouter_key_set: boolean
  openrouter_primary_model: string
  openrouter_fallback_model: string
  default_queries: string[]
  default_locations: string[]
  company_watchlist: string[]
  resume_filename: string | null
  resume_uploaded_at: string | null
  scraper_intervals: Record<string, number>
  scraper_enabled: Record<string, boolean>
}

export const fetchSettings = () =>
  api.get<Settings>('/settings').then((r) => r.data)

export const updateSettings = (data: any) =>
  api.post<Settings>('/settings', data).then((r) => r.data)

export const uploadResume = (file: File) => {
  const formData = new FormData()
  formData.append('file', file)
  return api.post('/resume/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then((r) => r.data)
}

// --- Saved Searches ---
export interface SavedSearch {
  id: number
  name: string
  query_params: Record<string, any>
  alert_enabled: boolean
  created_at: string
}

export const fetchSavedSearches = () =>
  api.get<SavedSearch[]>('/saved-searches').then((r) => r.data)

export const createSavedSearch = (data: { name: string; query_params: Record<string, any>; alert_enabled?: boolean }) =>
  api.post<SavedSearch>('/saved-searches', data).then((r) => r.data)

export const deleteSavedSearch = (id: number) =>
  api.delete(`/saved-searches/${id}`).then((r) => r.data)

// --- Copilot ---
export const streamCopilot = async function* (tool: string, jobId: string) {
  const resp = await fetch('/api/copilot', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ tool, job_id: jobId }),
  })
  const reader = resp.body?.getReader()
  if (!reader) return
  const decoder = new TextDecoder()
  let buffer = ''
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try {
          const data = JSON.parse(line.slice(6))
          if (data.content) yield data.content
          if (data.done || data.error) return
        } catch {}
      }
    }
  }
}

// --- SSE ---
export function connectSSE(onEvent: (event: any) => void): EventSource {
  const es = new EventSource('/api/scraper/stream')
  es.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data)
      onEvent(data)
    } catch {}
  }
  return es
}

export default api
