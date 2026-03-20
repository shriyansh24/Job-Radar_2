import {
  Briefcase,
  Clock,
  PaperPlaneTilt,
  TrendUp,
} from "@phosphor-icons/react";
import React, { Suspense } from "react";
import { useQuery } from "@tanstack/react-query";
import { analyticsApi } from "../api/analytics";
import Card from "../components/ui/Card";
import StatCard from "../components/ui/StatCard";
import Skeleton from "../components/ui/Skeleton";
import { cn } from "../lib/utils";

// Lazy-load recharts chart components to defer the large recharts bundle
// until the charts section is actually rendered (Fix 3)
const Charts = React.lazy(() => import('../components/analytics/AnalyticsCharts'));

const ANALYTICS_STALE_TIME = 10 * 60 * 1000; // 10 minutes — analytics data changes slowly (Fix 5)

function ChartsSkeleton() {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {Array.from({ length: 4 }).map((_, i) => (
        <Card key={i}>
          <Skeleton variant="text" className="w-1/3 h-4 mb-4" />
          <Skeleton variant="rect" className="w-full h-64" />
        </Card>
      ))}
    </div>
  );
}

export default function Analytics() {
  // Fix 5: All 5 useQuery calls get staleTime: 10 minutes since analytics data changes slowly
  const { data: overview, isLoading: loadingOverview } = useQuery({
    queryKey: ['analytics', 'overview'],
    queryFn: () => analyticsApi.overview().then((r) => r.data),
    staleTime: ANALYTICS_STALE_TIME,
  });

  const { data: daily } = useQuery({
    queryKey: ['analytics', 'daily'],
    queryFn: () => analyticsApi.daily(30).then((r) => r.data),
    staleTime: ANALYTICS_STALE_TIME,
  });

  const { data: sources } = useQuery({
    queryKey: ['analytics', 'sources'],
    queryFn: () => analyticsApi.sources().then((r) => r.data),
    staleTime: ANALYTICS_STALE_TIME,
  });

  const { data: skills } = useQuery({
    queryKey: ['analytics', 'skills'],
    queryFn: () => analyticsApi.skills(10).then((r) => r.data),
    staleTime: ANALYTICS_STALE_TIME,
  });

  const { data: funnel } = useQuery({
    queryKey: ['analytics', 'funnel'],
    queryFn: () => analyticsApi.funnel().then((r) => r.data),
    staleTime: ANALYTICS_STALE_TIME,
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

      {/* Fix 3: Suspense boundary around chart section so recharts loads lazily */}
      <Suspense fallback={<ChartsSkeleton />}>
        <Charts daily={daily} funnel={funnel} sources={sources} skills={skills} />
      </Suspense>

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
