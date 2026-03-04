import { useQuery, useMutation, useQueryClient, keepPreviousData } from '@tanstack/react-query'
import { Filter, LayoutGrid, List } from 'lucide-react'
import { fetchJobs, updateJob, type JobListResponse } from '../api/client'
import { useJobStore } from '../store/useJobStore'
import JobFilters from '../components/jobs/JobFilters'
import JobList from '../components/jobs/JobList'
import JobDetailPanel from '../components/jobs/JobDetailPanel'
import { cn } from '../lib/utils'

export default function JobBoard() {
  const queryClient = useQueryClient()
  const {
    filters, selectedJobId, setSelectedJobId,
    viewMode, setViewMode,
    isFilterPanelOpen, setIsFilterPanelOpen,
  } = useJobStore()

  const { data, isLoading } = useQuery<JobListResponse>({
    queryKey: ['jobs', filters],
    queryFn: () => fetchJobs(filters),
    placeholderData: keepPreviousData,
  })

  const starMutation = useMutation({
    mutationFn: ({ id, starred }: { id: string; starred: boolean }) =>
      updateJob(id, { is_starred: starred }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['jobs'] }),
  })

  const jobs = data?.jobs || []
  const total = data?.total || 0

  return (
    <div className="flex h-full -m-6">
      {/* Filters sidebar */}
      <JobFilters />

      {/* Main content */}
      <div className="flex-1 flex flex-col">
        {/* Toolbar */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-border">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setIsFilterPanelOpen(!isFilterPanelOpen)}
              className={cn(
                'p-1.5 rounded border transition-colors',
                isFilterPanelOpen
                  ? 'border-accent text-accent'
                  : 'border-border text-text-secondary hover:text-text-primary'
              )}
            >
              <Filter size={14} />
            </button>
            <span className="text-sm text-text-secondary">
              <span className="font-mono text-text-primary">{total.toLocaleString()}</span> jobs
              {filters.q && <span> matching "{filters.q}"</span>}
            </span>
          </div>

          <div className="flex items-center gap-2">
            <select
              value={filters.sort_by || 'scraped_at'}
              onChange={(e) => useJobStore.getState().setFilters({ sort_by: e.target.value })}
              className="bg-elevated border border-border rounded-lg px-2 py-1 text-xs text-text-primary focus:outline-none"
            >
              <option value="scraped_at">Recent</option>
              <option value="match_score">Match Score</option>
              <option value="posted_at">Posted Date</option>
              <option value="salary_max">Salary</option>
            </select>

            <div className="flex border border-border rounded-lg overflow-hidden">
              <button
                onClick={() => setViewMode('list')}
                className={cn(
                  'p-1.5',
                  viewMode === 'list' ? 'bg-elevated text-text-primary' : 'text-text-secondary'
                )}
              >
                <List size={14} />
              </button>
              <button
                onClick={() => setViewMode('grid')}
                className={cn(
                  'p-1.5',
                  viewMode === 'grid' ? 'bg-elevated text-text-primary' : 'text-text-secondary'
                )}
              >
                <LayoutGrid size={14} />
              </button>
            </div>
          </div>
        </div>

        {/* Job list */}
        <div className="flex-1 flex overflow-hidden">
          <div className="flex-1 overflow-hidden flex flex-col">
            {isLoading ? (
              <div className="flex-1 flex items-center justify-center">
                <div className="text-text-secondary text-sm">Loading jobs...</div>
              </div>
            ) : (
              <JobList
                jobs={jobs}
                selectedJobId={selectedJobId}
                onSelect={setSelectedJobId}
                onStar={(id, starred) => starMutation.mutate({ id, starred })}
              />
            )}

            {/* Pagination */}
            {data && data.total > data.limit && (
              <div className="flex items-center justify-between px-4 py-3 border-t border-border">
                <button
                  onClick={() =>
                    useJobStore.getState().setFilters({ page: Math.max(1, (filters.page || 1) - 1) })
                  }
                  disabled={(filters.page || 1) <= 1}
                  className="px-3 py-1 text-xs border border-border rounded-lg text-text-secondary hover:text-text-primary disabled:opacity-50"
                >
                  Previous
                </button>
                <span className="text-xs text-text-secondary font-mono">
                  Page {filters.page || 1} of {Math.ceil(data.total / data.limit)}
                </span>
                <button
                  onClick={() =>
                    useJobStore.getState().setFilters({ page: (filters.page || 1) + 1 })
                  }
                  disabled={!data.has_more}
                  className="px-3 py-1 text-xs border border-border rounded-lg text-text-secondary hover:text-text-primary disabled:opacity-50"
                >
                  Next
                </button>
              </div>
            )}
          </div>

          {/* Detail panel */}
          {selectedJobId && (
            <JobDetailPanel
              jobId={selectedJobId}
              onClose={() => setSelectedJobId(null)}
            />
          )}
        </div>
      </div>
    </div>
  )
}
