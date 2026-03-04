import { Activity } from 'lucide-react'
import { useJobStore } from '../../store/useJobStore'
import { cn } from '../../lib/utils'

export default function TopBar() {
  const { isScraperRunning, totalJobCount, isResumeActive } = useJobStore()

  return (
    <header className="h-14 bg-surface border-b border-border flex items-center justify-between px-6">
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-lg text-text-primary">JobRadar</span>
          <span
            className={cn(
              'w-2 h-2 rounded-full',
              isScraperRunning ? 'bg-accent animate-pulse' : 'bg-border'
            )}
          />
        </div>
        <span className="font-mono text-sm text-text-secondary">
          {totalJobCount.toLocaleString()} jobs
        </span>
      </div>

      <div className="flex items-center gap-4">
        {/* Scraper status pill */}
        <div
          className={cn(
            'flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium border',
            isScraperRunning
              ? 'text-accent-green border-accent-green/30 bg-accent-green/10'
              : 'text-text-secondary border-border bg-elevated'
          )}
        >
          <Activity size={12} />
          {isScraperRunning ? 'Live' : 'Idle'}
        </div>

        {/* Resume indicator */}
        {isResumeActive && (
          <div className="flex items-center gap-2 text-xs text-text-secondary">
            <span className="w-1.5 h-1.5 rounded-full bg-accent-green" />
            Resume: Active
          </div>
        )}
      </div>
    </header>
  )
}
