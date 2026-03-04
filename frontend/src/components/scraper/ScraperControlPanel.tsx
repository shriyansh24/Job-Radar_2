import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Play, Loader2 } from 'lucide-react'
import { fetchScraperStatus, triggerScraper } from '../../api/client'
import { cn, timeAgo } from '../../lib/utils'
import toast from 'react-hot-toast'

const SOURCES = ['serpapi', 'greenhouse', 'lever', 'ashby', 'jobspy']

export default function ScraperControlPanel() {
  const [runningSource, setRunningSource] = useState<string | null>(null)

  const { data: status } = useQuery({
    queryKey: ['scraper-status'],
    queryFn: fetchScraperStatus,
    refetchInterval: 5000,
  })

  const handleRun = async (source: string) => {
    setRunningSource(source)
    try {
      await triggerScraper(source)
      toast.success(`${source} scraper started`)
    } catch {
      toast.error(`Failed to start ${source} scraper`)
    }
    setRunningSource(null)
  }

  return (
    <div className="bg-surface border border-border rounded-xl p-5">
      <h2 className="text-sm font-semibold mb-4">Last Scraper Runs</h2>
      <table className="w-full text-xs">
        <thead>
          <tr className="text-text-secondary border-b border-border">
            <th className="text-left py-2">Source</th>
            <th className="text-right py-2">Found</th>
            <th className="text-right py-2">New</th>
            <th className="text-right py-2">Status</th>
            <th className="text-right py-2">When</th>
            <th className="text-right py-2"></th>
          </tr>
        </thead>
        <tbody>
          {status?.runs?.slice(0, 10).map((run) => (
            <tr key={run.id} className="border-b border-border/50">
              <td className="py-2 capitalize">{run.source}</td>
              <td className="py-2 text-right font-mono">{run.jobs_found}</td>
              <td className="py-2 text-right font-mono text-accent-green">{run.jobs_new}</td>
              <td className="py-2 text-right">
                <span
                  className={cn(
                    'px-1.5 py-0.5 rounded text-[10px]',
                    run.status === 'completed' && 'text-accent-green bg-accent-green/10',
                    run.status === 'running' && 'text-accent-amber bg-accent-amber/10',
                    run.status === 'failed' && 'text-accent-red bg-accent-red/10'
                  )}
                >
                  {run.status}
                </span>
              </td>
              <td className="py-2 text-right font-mono text-text-secondary">
                {timeAgo(run.started_at)}
              </td>
              <td className="py-2 text-right">
                <button
                  onClick={() => handleRun(run.source)}
                  disabled={runningSource === run.source}
                  className="p-1 rounded hover:bg-elevated text-text-secondary disabled:opacity-50"
                >
                  {runningSource === run.source ? (
                    <Loader2 size={12} className="animate-spin" />
                  ) : (
                    <Play size={12} />
                  )}
                </button>
              </td>
            </tr>
          ))}
          {(!status?.runs || status.runs.length === 0) && (
            <tr>
              <td colSpan={6} className="py-4 text-center text-text-secondary">
                No scraper runs yet
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  )
}
