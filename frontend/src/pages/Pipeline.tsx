import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchJobs, updateJob } from '../api/client'
import KanbanBoard from '../components/pipeline/KanbanBoard'
import toast from 'react-hot-toast'

export default function Pipeline() {
  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['jobs', 'pipeline'],
    queryFn: () =>
      fetchJobs({
        status: 'saved,applied,phone_screen,interview,final_round,offer,rejected,ghosted',
        limit: 200,
        sort_by: 'last_updated',
        sort_dir: 'desc',
      }),
  })

  const mutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) =>
      updateJob(id, { status }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] })
      queryClient.invalidateQueries({ queryKey: ['stats'] })
    },
    onError: () => {
      toast.error('Failed to update job status')
      queryClient.invalidateQueries({ queryKey: ['jobs', 'pipeline'] })
    },
  })

  const handleMoveJob = (jobId: string, newStatus: string) => {
    // Optimistic update
    queryClient.setQueryData(['jobs', 'pipeline'], (old: any) => {
      if (!old) return old
      return {
        ...old,
        jobs: old.jobs.map((j: any) =>
          j.job_id === jobId ? { ...j, status: newStatus } : j
        ),
      }
    })
    mutation.mutate({ id: jobId, status: newStatus })
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-text-secondary">Loading pipeline...</div>
      </div>
    )
  }

  const jobs = data?.jobs || []

  return (
    <div className="h-full">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-lg font-semibold">Application Pipeline</h1>
        <span className="text-sm text-text-secondary font-mono">
          {jobs.length} tracked
        </span>
      </div>
      <KanbanBoard jobs={jobs} onMoveJob={handleMoveJob} />
    </div>
  )
}
