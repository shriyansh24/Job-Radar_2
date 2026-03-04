import { useQuery } from '@tanstack/react-query'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts'
import { fetchStats, fetchJobs } from '../api/client'
import ScoreRing from '../components/jobs/ScoreRing'
import { SOURCE_COLORS } from '../lib/constants'
import { timeAgo, getInitials, cn } from '../lib/utils'

export default function Dashboard() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['stats'],
    queryFn: fetchStats,
    refetchInterval: 30_000,
  })

  const { data: topMatches } = useQuery({
    queryKey: ['jobs', 'top-matches'],
    queryFn: () => fetchJobs({ sort_by: 'match_score', sort_dir: 'desc', limit: 10 }),
  })

  if (isLoading || !stats) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-text-secondary">Loading dashboard...</div>
      </div>
    )
  }

  const statCards = [
    { label: 'Total Jobs', value: stats.total_jobs, color: 'text-text-primary' },
    { label: 'New Today', value: stats.new_today, color: 'text-accent-green' },
    { label: 'Applied', value: stats.by_status?.applied || 0, color: 'text-accent-cyan' },
    { label: 'Avg Match', value: stats.avg_match_score ? `${Math.round(stats.avg_match_score)}%` : 'N/A', color: 'text-accent' },
  ]

  const sourceData = Object.entries(stats.by_source).map(([source, count]) => ({
    source,
    count,
  }))

  const skillsData = stats.top_skills.slice(0, 15).map((s) => ({
    skill: s.skill,
    count: s.count,
  }))

  return (
    <div className="space-y-6">
      {/* Stat cards */}
      <div className="grid grid-cols-4 gap-4">
        {statCards.map((card) => (
          <div key={card.label} className="bg-surface border border-border rounded-xl p-5">
            <div className="text-xs text-text-secondary mb-2">{card.label}</div>
            <div className={cn('text-2xl font-mono font-bold', card.color)}>
              {typeof card.value === 'number' ? card.value.toLocaleString() : card.value}
            </div>
          </div>
        ))}
      </div>

      {/* Two-column layout */}
      <div className="grid grid-cols-5 gap-6">
        {/* Top Matches */}
        <div className="col-span-3 bg-surface border border-border rounded-xl p-5">
          <h2 className="text-sm font-semibold mb-4">Top Matches</h2>
          <div className="space-y-2">
            {topMatches?.jobs?.length ? (
              topMatches.jobs.map((job) => (
                <div
                  key={job.job_id}
                  className="flex items-center gap-3 p-3 rounded-lg hover:bg-elevated transition-colors"
                >
                  <div className="w-8 h-8 rounded-lg bg-elevated border border-border flex items-center justify-center flex-shrink-0 overflow-hidden">
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
                      <span className="text-xs font-semibold text-text-secondary">
                        {getInitials(job.company_name)}
                      </span>
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium truncate">{job.title}</div>
                    <div className="text-xs text-text-secondary truncate">
                      {job.company_name}
                      {job.location_city && ` \u00b7 ${job.location_city}`}
                    </div>
                  </div>
                  <span
                    className={cn(
                      'text-xs px-1.5 py-0.5 rounded border capitalize',
                      SOURCE_COLORS[job.source] || 'text-text-secondary border-border'
                    )}
                  >
                    {job.source}
                  </span>
                  <ScoreRing score={job.match_score} size={32} strokeWidth={2} />
                  <span className="text-xs text-text-secondary font-mono flex-shrink-0 w-16 text-right">
                    {timeAgo(job.posted_at || job.scraped_at)}
                  </span>
                </div>
              ))
            ) : (
              <div className="text-center text-text-secondary py-8 text-sm">
                No jobs yet. Run a scraper to get started.
              </div>
            )}
          </div>
        </div>

        {/* Right column */}
        <div className="col-span-2 space-y-6">
          {/* Source Activity */}
          <div className="bg-surface border border-border rounded-xl p-5">
            <h2 className="text-sm font-semibold mb-4">Jobs by Source</h2>
            {sourceData.length > 0 ? (
              <ResponsiveContainer width="100%" height={160}>
                <BarChart data={sourceData}>
                  <XAxis dataKey="source" tick={{ fontSize: 11, fill: '#888' }} />
                  <YAxis tick={{ fontSize: 11, fill: '#888' }} />
                  <Tooltip
                    contentStyle={{
                      background: '#111',
                      border: '1px solid #333',
                      borderRadius: 8,
                      fontSize: 12,
                    }}
                  />
                  <Bar dataKey="count" fill="#0070F3" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="text-center text-text-secondary py-8 text-sm">No data yet</div>
            )}
          </div>

          {/* Top Skills */}
          <div className="bg-surface border border-border rounded-xl p-5">
            <h2 className="text-sm font-semibold mb-4">Top Skills in Market</h2>
            {skillsData.length > 0 ? (
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={skillsData} layout="vertical">
                  <XAxis type="number" tick={{ fontSize: 11, fill: '#888' }} />
                  <YAxis
                    dataKey="skill"
                    type="category"
                    width={100}
                    tick={{ fontSize: 11, fill: '#888' }}
                  />
                  <Tooltip
                    contentStyle={{
                      background: '#111',
                      border: '1px solid #333',
                      borderRadius: 8,
                      fontSize: 12,
                    }}
                  />
                  <Bar dataKey="count" fill="#10B981" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="text-center text-text-secondary py-8 text-sm">No enriched data yet</div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
