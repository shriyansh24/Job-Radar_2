import { useQuery } from '@tanstack/react-query'
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, BarChart, Bar,
} from 'recharts'
import { fetchStats } from '../api/client'

const COLORS = ['#0070F3', '#10B981', '#F5A623', '#E00000', '#3291FF', '#a855f7', '#ec4899']

export default function Analytics() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['stats'],
    queryFn: fetchStats,
    refetchInterval: 60_000,
  })

  if (isLoading || !stats) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-text-secondary">Loading analytics...</div>
      </div>
    )
  }

  // Experience level data
  const expData = Object.entries(stats.by_experience_level).map(([level, count]) => ({
    name: level,
    value: count,
  }))

  // Top companies
  const companyData = stats.top_companies.slice(0, 20)

  // Skills heatmap data
  const skillsData = stats.top_skills.slice(0, 30)

  // Application funnel
  const funnelData = [
    { stage: 'Saved', count: stats.by_status?.saved || 0 },
    { stage: 'Applied', count: stats.by_status?.applied || 0 },
    { stage: 'Phone Screen', count: stats.by_status?.phone_screen || 0 },
    { stage: 'Interview', count: stats.by_status?.interview || stats.by_status?.interviewing || 0 },
    { stage: 'Offer', count: stats.by_status?.offer || 0 },
  ]

  const tooltipStyle = {
    contentStyle: {
      background: '#111',
      border: '1px solid #333',
      borderRadius: 8,
      fontSize: 12,
      color: '#EDEDED',
    },
  }

  return (
    <div className="space-y-6">
      <h1 className="text-lg font-semibold">Analytics</h1>

      {/* Row 1: Jobs over time */}
      <div className="bg-surface border border-border rounded-xl p-5">
        <h2 className="text-sm font-semibold mb-4">Jobs Per Day (Last 30 Days)</h2>
        {stats.jobs_over_time.length > 0 ? (
          <ResponsiveContainer width="100%" height={250}>
            <AreaChart data={stats.jobs_over_time}>
              <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#888' }} />
              <YAxis tick={{ fontSize: 11, fill: '#888' }} />
              <Tooltip {...tooltipStyle} />
              {Object.keys(stats.by_source).map((source, i) => (
                <Area
                  key={source}
                  type="monotone"
                  dataKey={source}
                  stackId="1"
                  stroke={COLORS[i % COLORS.length]}
                  fill={COLORS[i % COLORS.length]}
                  fillOpacity={0.3}
                />
              ))}
            </AreaChart>
          </ResponsiveContainer>
        ) : (
          <div className="text-center text-text-secondary py-12 text-sm">No data yet</div>
        )}
      </div>

      {/* Row 2: Experience level pie + Top companies bar */}
      <div className="grid grid-cols-2 gap-6">
        <div className="bg-surface border border-border rounded-xl p-5">
          <h2 className="text-sm font-semibold mb-4">By Experience Level</h2>
          {expData.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={expData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  dataKey="value"
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                >
                  {expData.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip {...tooltipStyle} />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="text-center text-text-secondary py-12 text-sm">No enriched data yet</div>
          )}
        </div>

        <div className="bg-surface border border-border rounded-xl p-5">
          <h2 className="text-sm font-semibold mb-4">Top Companies</h2>
          {companyData.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={companyData} layout="vertical">
                <XAxis type="number" tick={{ fontSize: 11, fill: '#888' }} />
                <YAxis
                  dataKey="name"
                  type="category"
                  width={120}
                  tick={{ fontSize: 10, fill: '#888' }}
                />
                <Tooltip {...tooltipStyle} />
                <Bar dataKey="count" fill="#0070F3" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="text-center text-text-secondary py-12 text-sm">No data yet</div>
          )}
        </div>
      </div>

      {/* Row 3: Skills heatmap */}
      <div className="bg-surface border border-border rounded-xl p-5">
        <h2 className="text-sm font-semibold mb-4">Top Skills</h2>
        {skillsData.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {skillsData.map((s) => {
              const maxCount = skillsData[0]?.count || 1
              const opacity = 0.2 + (s.count / maxCount) * 0.8
              return (
                <div
                  key={s.skill}
                  className="px-3 py-1.5 rounded-lg text-xs font-medium"
                  style={{
                    background: `rgba(0, 112, 243, ${opacity})`,
                    color: opacity > 0.5 ? '#fff' : '#EDEDED',
                  }}
                >
                  {s.skill}
                  <span className="ml-1.5 font-mono opacity-70">{s.count}</span>
                </div>
              )
            })}
          </div>
        ) : (
          <div className="text-center text-text-secondary py-8 text-sm">No enriched data yet</div>
        )}
      </div>

      {/* Row 4: Application funnel */}
      <div className="bg-surface border border-border rounded-xl p-5">
        <h2 className="text-sm font-semibold mb-4">Application Funnel</h2>
        {funnelData.some((d) => d.count > 0) ? (
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={funnelData}>
              <XAxis dataKey="stage" tick={{ fontSize: 11, fill: '#888' }} />
              <YAxis tick={{ fontSize: 11, fill: '#888' }} />
              <Tooltip {...tooltipStyle} />
              <Bar dataKey="count" fill="#10B981" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="text-center text-text-secondary py-12 text-sm">
            Start tracking applications to see funnel data
          </div>
        )}
      </div>
    </div>
  )
}
