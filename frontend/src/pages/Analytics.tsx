import {
  Briefcase,
  Clock,
  PaperPlaneTilt,
  TrendUp,
} from "@phosphor-icons/react";
import { useQuery } from "@tanstack/react-query";
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts';
import { analyticsApi } from "../api/analytics";
import Card from "../components/ui/Card";
import StatCard from "../components/ui/StatCard";
import Skeleton from "../components/ui/Skeleton";
import { cn } from "../lib/utils";

const COLORS = ["#0ea5e9", "#10b981", "#f59e0b", "#ef4444", "#a855f7", "#22c55e"];

const tooltipStyle = {
  contentStyle: {
    backgroundColor: "var(--color-bg-secondary)",
    border: "1px solid var(--color-border)",
    borderRadius: "0.75rem",
    color: "var(--color-text-primary)",
    fontSize: "0.75rem",
  },
};

export default function Analytics() {
  const { data: overview, isLoading: loadingOverview } = useQuery({
    queryKey: ['analytics', 'overview'],
    queryFn: () => analyticsApi.overview().then((r) => r.data),
  });

  const { data: daily } = useQuery({
    queryKey: ['analytics', 'daily'],
    queryFn: () => analyticsApi.daily(30).then((r) => r.data),
  });

  const { data: sources } = useQuery({
    queryKey: ['analytics', 'sources'],
    queryFn: () => analyticsApi.sources().then((r) => r.data),
  });

  const { data: skills } = useQuery({
    queryKey: ['analytics', 'skills'],
    queryFn: () => analyticsApi.skills(10).then((r) => r.data),
  });

  const { data: funnel } = useQuery({
    queryKey: ['analytics', 'funnel'],
    queryFn: () => analyticsApi.funnel().then((r) => r.data),
  });

  const o = overview || {
    total_jobs: 0,
    total_applications: 0,
    response_rate: 0,
    avg_days_to_response: 0,
    total_interviews: 0,
    total_offers: 0,
  };

  return (
    <div className="space-y-6">
      <div>
        <div className="text-xs font-medium text-text-muted tracking-tight">
          Insights
        </div>
        <h1 className="mt-1 text-2xl font-semibold tracking-tight text-text-primary">
          Analytics
        </h1>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {loadingOverview ? (
          Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} variant="rect" className="h-24" />
          ))
        ) : (
          <>
            <StatCard
              icon={<Briefcase size={20} weight="bold" className="text-accent-primary" />}
              title="Total Jobs"
              value={o.total_jobs.toLocaleString()}
            />
            <StatCard
              icon={<PaperPlaneTilt size={20} weight="bold" className="text-accent-primary" />}
              title="Applications"
              value={o.total_applications.toLocaleString()}
            />
            <StatCard
              icon={<TrendUp size={20} weight="bold" className="text-accent-success" />}
              title="Response Rate"
              value={`${(o.response_rate * 100).toFixed(0)}%`}
            />
            <StatCard
              icon={<Clock size={20} weight="bold" className="text-accent-warning" />}
              title="Avg Days to Response"
              value={o.avg_days_to_response.toFixed(1)}
            />
          </>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Jobs Over Time */}
        <Card>
          <h2 className="text-sm font-semibold text-text-primary mb-4">Jobs Scraped (Last 30 Days)</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={daily || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                <XAxis dataKey="date" tick={{ fontSize: 11, fill: 'var(--color-text-muted)' }} tickFormatter={(d: string) => d.slice(5)} />
                <YAxis tick={{ fontSize: 11, fill: 'var(--color-text-muted)' }} />
                <Tooltip {...tooltipStyle} />
                <Line type="monotone" dataKey="jobs_scraped" stroke="var(--color-accent-primary)" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Application Funnel */}
        <Card>
          <h2 className="text-sm font-semibold text-text-primary mb-4">Application Funnel</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={funnel || []} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                <XAxis type="number" tick={{ fontSize: 11, fill: 'var(--color-text-muted)' }} />
                <YAxis type="category" dataKey="stage" tick={{ fontSize: 11, fill: 'var(--color-text-secondary)' }} width={100} />
                <Tooltip {...tooltipStyle} />
                <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                  {(funnel || []).map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Jobs by Source */}
        <Card>
          <h2 className="text-sm font-semibold text-text-primary mb-4">Jobs by Source</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={sources || []}
                  dataKey="total_jobs"
                  nameKey="source"
                  cx="50%"
                  cy="50%"
                  outerRadius={90}
                  label={({ name, percent }: { name?: string; percent?: number }) => `${name ?? ''} ${((percent ?? 0) * 100).toFixed(0)}%`}
                  labelLine={false}
                >
                  {(sources || []).map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip {...tooltipStyle} />
                <Legend wrapperStyle={{ fontSize: '0.75rem', color: '#a0a0b8' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Top Skills */}
        <Card>
          <h2 className="text-sm font-semibold text-text-primary mb-4">Top Skills Requested</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={skills || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                <XAxis dataKey="skill" tick={{ fontSize: 10, fill: 'var(--color-text-muted)' }} interval={0} angle={-30} textAnchor="end" height={60} />
                <YAxis tick={{ fontSize: 11, fill: 'var(--color-text-muted)' }} />
                <Tooltip {...tooltipStyle} />
                <Bar dataKey="count" fill="var(--color-accent-primary)" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      {/* Source Quality Table */}
      {sources && sources.length > 0 && (
        <Card>
          <h2 className="text-sm font-semibold text-text-primary mb-4">Source Quality</h2>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border">
                  <th className="px-4 py-2 text-left text-xs font-medium text-text-muted uppercase">Source</th>
                  <th className="px-4 py-2 text-right text-xs font-medium text-text-muted uppercase">Total Jobs</th>
                  <th className="px-4 py-2 text-right text-xs font-medium text-text-muted uppercase">Quality Score</th>
                  <th className="px-4 py-2 text-right text-xs font-medium text-text-muted uppercase">Avg Match</th>
                </tr>
              </thead>
              <tbody>
                {sources.map((s) => (
                  <tr key={s.source} className="border-b border-border/50">
                    <td className="px-4 py-2.5 text-sm text-text-primary font-medium">{s.source}</td>
                    <td className="px-4 py-2.5 text-sm text-text-secondary text-right">{s.total_jobs}</td>
                    <td className="px-4 py-2.5 text-sm text-right">
                      <span className={cn(
                        s.quality_score >= 0.8 ? 'text-accent-success' : s.quality_score >= 0.5 ? 'text-accent-warning' : 'text-accent-danger'
                      )}>
                        {(s.quality_score * 100).toFixed(0)}%
                      </span>
                    </td>
                    <td className="px-4 py-2.5 text-sm text-text-secondary text-right">
                      {s.avg_match_score ? `${(s.avg_match_score * 100).toFixed(0)}%` : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
}
