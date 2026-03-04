import { STATUS_COLORS, STATUS_BG_COLORS } from '../../lib/constants'
import { cn } from '../../lib/utils'

interface JobStatusBadgeProps {
  status: string
}

export default function JobStatusBadge({ status }: JobStatusBadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium capitalize',
        STATUS_COLORS[status] || 'text-text-secondary',
        STATUS_BG_COLORS[status] || 'bg-elevated'
      )}
    >
      <span
        className={cn(
          'w-1.5 h-1.5 rounded-full',
          status === 'new' && 'bg-accent-green',
          status === 'saved' && 'bg-accent-amber',
          status === 'applied' && 'bg-accent-cyan',
          status === 'interviewing' && 'bg-purple-400',
          status === 'offer' && 'bg-pink-400',
          status === 'rejected' && 'bg-accent-red',
          status === 'ghosted' && 'bg-slate-500'
        )}
      />
      {status.replace('_', ' ')}
    </span>
  )
}
