import { useRef } from 'react'
import { useVirtualizer } from '@tanstack/react-virtual'
import type { Job } from '../../api/client'
import JobCard from './JobCard'

interface JobListProps {
  jobs: Job[]
  selectedJobId: string | null
  onSelect: (id: string) => void
  onStar: (id: string, starred: boolean) => void
}

export default function JobList({ jobs, selectedJobId, onSelect, onStar }: JobListProps) {
  const parentRef = useRef<HTMLDivElement>(null)

  const virtualizer = useVirtualizer({
    count: jobs.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 120,
    overscan: 10,
  })

  if (jobs.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <p className="text-text-secondary text-sm">No jobs match your filters</p>
          <p className="text-text-secondary text-xs mt-1">Try adjusting your search criteria</p>
        </div>
      </div>
    )
  }

  return (
    <div ref={parentRef} className="flex-1 overflow-auto">
      <div
        style={{
          height: `${virtualizer.getTotalSize()}px`,
          width: '100%',
          position: 'relative',
        }}
      >
        {virtualizer.getVirtualItems().map((virtualItem) => {
          const job = jobs[virtualItem.index]
          return (
            <div
              key={virtualItem.key}
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                height: `${virtualItem.size}px`,
                transform: `translateY(${virtualItem.start}px)`,
              }}
              className="px-1 py-1"
            >
              <JobCard
                job={job}
                isSelected={job.job_id === selectedJobId}
                onClick={() => onSelect(job.job_id)}
                onStar={() => onStar(job.job_id, !job.is_starred)}
              />
            </div>
          )
        })}
      </div>
    </div>
  )
}
