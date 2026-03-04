import type { Job } from '../../api/client'
import { getInitials, timeAgo, cn } from '../../lib/utils'
import ScoreRing from '../jobs/ScoreRing'

interface KanbanCardProps {
  job: Job
}

export default function KanbanCard({ job }: KanbanCardProps) {
  return (
    <div className="p-3 bg-surface border border-border rounded-lg hover:border-border cursor-grab active:cursor-grabbing">
      <div className="flex items-start gap-2">
        <div className="w-7 h-7 rounded bg-elevated border border-border flex items-center justify-center flex-shrink-0 overflow-hidden">
          {job.company_logo_url ? (
            <img
              src={job.company_logo_url}
              alt=""
              className="w-full h-full object-contain"
              onError={(e) => {
                ;(e.target as HTMLImageElement).style.display = 'none'
              }}
            />
          ) : (
            <span className="text-[10px] font-semibold text-text-secondary">
              {getInitials(job.company_name)}
            </span>
          )}
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-xs font-medium truncate">{job.title}</p>
          <p className="text-[11px] text-text-secondary truncate">{job.company_name}</p>
        </div>
        <ScoreRing score={job.match_score} size={28} strokeWidth={2} />
      </div>
      {job.applied_at && (
        <div className="text-[10px] text-text-secondary font-mono mt-2">
          Applied {timeAgo(job.applied_at)}
        </div>
      )}
    </div>
  )
}
