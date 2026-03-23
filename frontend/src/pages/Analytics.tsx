import {
  Briefcase,
  Clock,
  PaperPlaneTilt,
  TrendUp,
} from "@phosphor-icons/react";
import { useQuery } from "@tanstack/react-query";
import { lazy, Suspense } from "react";
import { analyticsApi } from "../api/analytics";
import Skeleton from "../components/ui/Skeleton";
import { MetricStrip } from "../components/system/MetricStrip";
import { PageHeader } from "../components/system/PageHeader";
import { SectionHeader } from "../components/system/SectionHeader";
import { SplitWorkspace } from "../components/system/SplitWorkspace";
import { StateBlock } from "../components/system/StateBlock";
import { Surface } from "../components/system/Surface";
import { cn } from "../lib/utils";

const Charts = lazy(() => import("../components/analytics/AnalyticsCharts"));
const ANALYTICS_STALE_TIME = 10 * 60 * 1000;

function ChartsSkeleton() {
  return (
    <div className="grid gap-4 lg:grid-cols-2">
      {Array.from({ length: 4 }).map((_, index) => (
        <Surface key={index} tone="default" padding="md" radius="xl">
          <Skeleton variant="text" className="mb-4 h-4 w-1/3" />
          <Skeleton variant="rect" className="h-64 w-full" />
        </Surface>
      ))}
    </div>
  );
}

export default function Analytics() {
  const { data: overview, isLoading: loadingOverview } = useQuery({
    queryKey: ["analytics", "overview"],
    queryFn: () => analyticsApi.overview().then((response) => response.data),
    staleTime: ANALYTICS_STALE_TIME,
  });

  const { data: daily } = useQuery({
    queryKey: ["analytics", "daily"],
    queryFn: () => analyticsApi.daily(30).then((response) => response.data),
    staleTime: ANALYTICS_STALE_TIME,
  });

  const { data: sources } = useQuery({
    queryKey: ["analytics", "sources"],
    queryFn: () => analyticsApi.sources().then((response) => response.data),
    staleTime: ANALYTICS_STALE_TIME,
  });

  const { data: skills } = useQuery({
    queryKey: ["analytics", "skills"],
    queryFn: () => analyticsApi.skills(10).then((response) => response.data),
    staleTime: ANALYTICS_STALE_TIME,
  });

  const { data: funnel } = useQuery({
    queryKey: ["analytics", "funnel"],
    queryFn: () => analyticsApi.funnel().then((response) => response.data),
    staleTime: ANALYTICS_STALE_TIME,
  });

  const summary = overview ?? {
    total_jobs: 0,
    total_applications: 0,
    response_rate: 0,
    avg_days_to_response: 0,
    total_interviews: 0,
    total_offers: 0,
  };

  const metrics = [
    {
      key: "jobs",
      label: "Jobs",
      value: loadingOverview ? "…" : summary.total_jobs.toLocaleString(),
      hint: "Known opportunities in the workspace.",
      icon: <Briefcase size={18} weight="bold" />,
    },
    {
      key: "applications",
      label: "Applications",
      value: loadingOverview ? "…" : summary.total_applications.toLocaleString(),
      hint: "Applications tracked from search to outcome.",
      icon: <PaperPlaneTilt size={18} weight="bold" />,
    },
    {
      key: "responses",
      label: "Response rate",
      value: loadingOverview ? "…" : `${Math.round(summary.response_rate * 100)}%`,
      hint: "How often the market answers back.",
      icon: <TrendUp size={18} weight="bold" />,
    },
    {
      key: "latency",
      label: "Avg days to response",
      value: loadingOverview ? "…" : summary.avg_days_to_response.toFixed(1),
      hint: "Average time from application to a meaningful reply.",
      icon: <Clock size={18} weight="bold" />,
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Intelligence"
        title="Analytics"
        description="A dense, readable control surface for understanding discovery volume, applications, response quality, and source health."
        meta={
          <span className="text-xs text-muted-foreground">
            Metrics refresh slowly, so this page intentionally caches a little longer.
          </span>
        }
      />

      <MetricStrip items={metrics} />

      <SplitWorkspace
        primary={
          <div className="space-y-6">
            <SectionHeader
              title="Trend and funnel views"
              description="The heavy visualizations stay lazy-loaded so the page remains fast on first paint."
            />
            <Suspense fallback={<ChartsSkeleton />}>
              <Charts daily={daily} funnel={funnel} sources={sources} skills={skills} />
            </Suspense>
          </div>
        }
        secondary={
          <div className="space-y-6">
            <Surface tone="default" padding="md" radius="xl">
              <SectionHeader
                title="Source quality"
                description="Which channels are producing the most relevant roles."
              />
              {sources && sources.length ? (
                <div className="mt-4 overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-border/70 text-left text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
                        <th className="px-0 py-2">Source</th>
                        <th className="px-0 py-2 text-right">Jobs</th>
                        <th className="px-0 py-2 text-right">Quality</th>
                        <th className="px-0 py-2 text-right">Match</th>
                      </tr>
                    </thead>
                    <tbody>
                      {sources.map((source) => (
                        <tr key={source.source} className="border-b border-border/50">
                          <td className="py-3 text-sm font-medium text-foreground">{source.source}</td>
                          <td className="py-3 text-right text-sm text-muted-foreground">{source.total_jobs}</td>
                          <td className="py-3 text-right text-sm">
                            <span
                              className={cn(
                                source.quality_score >= 0.8
                                  ? "text-[var(--color-accent-success)]"
                                  : source.quality_score >= 0.5
                                    ? "text-[var(--color-accent-warning)]"
                                    : "text-[var(--color-accent-danger)]"
                              )}
                            >
                              {(source.quality_score * 100).toFixed(0)}%
                            </span>
                          </td>
                          <td className="py-3 text-right text-sm text-muted-foreground">
                            {source.avg_match_score ? `${(source.avg_match_score * 100).toFixed(0)}%` : "—"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <StateBlock
                  tone="muted"
                  title="No source quality yet"
                  description="Once scrapers and saved searches have data, the quality table will appear here."
                />
              )}
            </Surface>
          </div>
        }
      />
    </div>
  );
}
