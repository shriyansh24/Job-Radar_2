import { Star, MapPin, ExternalLink } from 'lucide-react'
import type { Job } from '../../api/client'
import { SOURCE_COLORS } from '../../lib/constants'
import { timeAgo, getInitials, cn } from '../../lib/utils'
import ScoreRing from './ScoreRing'
import JobStatusBadge from './JobStatusBadge'

interface JobCardProps {
  job: Job
  isSelected?: boolean
  onClick: () => void
  onStar: () => void
}

export default function JobCard({ job, isSelected, onClick, onStar }: JobCardProps) {
  const logoUrl = job.company_logo_url
  const sourceClass = SOURCE_COLORS[job.source] || 'text-text-secondary border-border bg-elevated'

  return (
    <div
      onClick={onClick}
      className={cn(
        'group p-4 border border-border rounded-lg cursor-pointer transition-all',
        isSelected
          ? 'bg-elevated border-accent/50'
          : 'bg-surface hover:bg-elevated hover:border-border'
      )}
    >
      <div className="flex items-start gap-3">
        {/* Company logo */}
        <div className="w-10 h-10 rounded-lg bg-elevated border border-border flex items-center justify-center flex-shrink-0 overflow-hidden">
          {logoUrl ? (
            <img
              src={logoUrl}
              alt={job.company_name}
              className="w-full h-full object-contain"
              onError={(e) => {
                ;(e.target as HTMLImageElement).style.display = 'none'
                ;(e.target as HTMLImageElement).nextElementSibling?.classList.remove('hidden')
              }}
            />
          ) : null}
          <span className={cn('text-xs font-semibold text-text-secondary', logoUrl && 'hidden')}>
            {getInitials(job.company_name)}
          </span>
        </div>

        <div className="flex-1 min-w-0">
          {/* Company + time */}
          <div className="flex items-center justify-between gap-2">
            <span className="text-xs text-text-secondary truncate">{job.company_name}</span>
            <span className="text-xs text-text-secondary font-mono flex-shrink-0">
              {timeAgo(job.posted_at || job.scraped_at)}
            </span>
          </div>

          {/* Title */}
          <h3 className="text-sm font-semibold text-text-primary mt-0.5 truncate">{job.title}</h3>

          {/* Location + Remote */}
          <div className="flex items-center gap-2 mt-1.5">
            {(job.location_city || job.location_state) && (
              <span className="flex items-center gap-1 text-xs text-text-secondary">
                <MapPin size={12} />
                {[job.location_city, job.location_state].filter(Boolean).join(', ')}
              </span>
            )}
            {job.remote_type && job.remote_type !== 'unknown' && (
              <span className="text-xs px-1.5 py-0.5 rounded bg-accent/10 text-accent capitalize">
                {job.remote_type}
              </span>
            )}
          </div>

          {/* Tags row */}
          <div className="flex items-center gap-2 mt-2 flex-wrap">
            {/* Source badge */}
            <span className={cn('text-xs px-1.5 py-0.5 rounded border capitalize', sourceClass)}>
              {job.source}
            </span>

            {/* Tech stack pills */}
            {job.tech_stack?.slice(0, 3).map((tech) => (
              <span key={tech} className="text-xs px-1.5 py-0.5 rounded bg-accent/10 text-accent">
                {tech}
              </span>
            ))}

            {/* Status */}
            <JobStatusBadge status={job.status} />
          </div>
        </div>

        {/* Right side: score + star */}
        <div className="flex flex-col items-center gap-2 flex-shrink-0">
          <ScoreRing score={job.match_score} size={36} strokeWidth={2.5} />
          <button
            onClick={(e) => {
              e.stopPropagation()
              onStar()
            }}
            className={cn(
              'p-1 rounded transition-colors',
              job.is_starred
                ? 'text-accent-amber'
                : 'text-text-secondary opacity-0 group-hover:opacity-100'
            )}
          >
            <Star size={14} fill={job.is_starred ? 'currentColor' : 'none'} />
          </button>
        </div>
      </div>
    </div>
  )
}
