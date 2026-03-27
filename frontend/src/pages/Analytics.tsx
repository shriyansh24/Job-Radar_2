import {
  Briefcase,
  Clock,
  DownloadSimple,
  PaperPlaneTilt,
  TrendUp,
} from "@phosphor-icons/react";
import { useQuery } from "@tanstack/react-query";
import { lazy, Suspense } from "react";
import type { ReactNode } from "react";
import { motion } from "framer-motion";
import { analyticsApi } from "../api/analytics";
import Badge from "../components/ui/Badge";
import Button from "../components/ui/Button";
import EmptyState from "../components/ui/EmptyState";
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
        <div key={index} className="border-2 border-border bg-card p-4 shadow-[var(--shadow-sm)]">
          <Skeleton variant="text" className="mb-4 h-4 w-1/3" />
          <Skeleton variant="rect" className="h-64 w-full" />
        </div>
      ))}
    </div>
  );
}

function SideStat({
  label,
  value,
  hint,
  icon,
  tone = "default",
}: {
  label: string;
  value: string;
  hint: string;
  icon: ReactNode;
  tone?: "default" | "success" | "warning";
}) {
  const toneClass = {
    default: "bg-card",
    success: "bg-[var(--color-accent-secondary-subtle)]",
    warning: "bg-[var(--color-accent-warning-subtle)]",
  }[tone];

  return (
    <Surface tone="default" padding="md" radius="xl" className={cn("h-full", toneClass)}>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
            {label}
          </div>
          <div className="mt-3 text-3xl font-black tracking-[-0.05em] text-text-primary">
            {value}
          </div>
          <p className="mt-2 text-sm leading-6 text-text-secondary">{hint}</p>
        </div>
        <div className="flex size-10 shrink-0 items-center justify-center border-2 border-border bg-background">
          {icon}
        </div>
      </div>
    </Surface>
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
      value: loadingOverview ? "..." : summary.total_jobs.toLocaleString(),
      hint: "Known opportunities in the workspace.",
      icon: <Briefcase size={18} weight="bold" />,
    },
    {
      key: "applications",
      label: "Applications",
      value: loadingOverview ? "..." : summary.total_applications.toLocaleString(),
      hint: "Applications tracked from search to outcome.",
      icon: <PaperPlaneTilt size={18} weight="bold" />,
    },
    {
      key: "responses",
      label: "Response rate",
      value: loadingOverview ? "..." : `${Math.round(summary.response_rate * 100)}%`,
      hint: "How often the market answers back.",
      icon: <TrendUp size={18} weight="bold" />,
      tone: "success" as const,
    },
    {
      key: "latency",
      label: "Avg days to response",
      value: loadingOverview ? "..." : summary.avg_days_to_response.toFixed(1),
      hint: "Average time from application to a meaningful reply.",
      icon: <Clock size={18} weight="bold" />,
      tone: "warning" as const,
    },
  ];

  return (
    <div className="space-y-6 px-4 py-4 sm:px-6 sm:py-6">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
        className="space-y-6"
      >
        <PageHeader
          eyebrow="Intelligence"
          title="Analytics"
          description="A compact control surface for discovery volume, application outcomes, response quality, and source health."
          actions={
            <>
              <Button variant="secondary" size="sm" icon={<Clock size={14} weight="bold" />}>
                Last 30 days
              </Button>
              <Button variant="primary" size="sm" icon={<DownloadSimple size={14} weight="bold" />}>
                Export PDF
              </Button>
            </>
          }
          meta={
            <>
              <Badge variant="info" size="sm">
                Live charts
              </Badge>
              <Badge variant="success" size="sm">
                Source feed
              </Badge>
            </>
          }
        />

        <MetricStrip items={metrics} />
      </motion.div>

      <SplitWorkspace
        primary={
          <div className="space-y-4">
            <Surface tone="default" padding="lg" radius="xl">
              <SectionHeader
                title="Trend slab"
                description="History, response rate, and source mix share one surface so the signal stays easy to compare."
                action={<Badge variant="info">Lazy loaded</Badge>}
              />
              <div className="mt-5">
                <Suspense fallback={<ChartsSkeleton />}>
                  <Charts daily={daily} funnel={funnel} sources={sources} skills={skills} />
                </Suspense>
              </div>
            </Surface>

            <Surface tone="subtle" padding="lg" radius="xl">
              <SectionHeader
                title="Skills pulse"
                description="The most frequent skill signals coming back from recent jobs."
                action={<Badge variant={skills?.length ? "success" : "default"}>{skills?.length ?? 0}</Badge>}
              />
              <div className="mt-4 flex flex-wrap gap-2">
                {skills?.length ? (
                  skills.slice(0, 8).map((skill) => (
                    <span
                      key={skill.skill}
                      className="brutal-chip bg-[var(--color-bg-secondary)] text-text-primary"
                    >
                      {skill.skill}
                    </span>
                  ))
                ) : (
                  <EmptyState
                    icon={<Briefcase size={32} weight="bold" />}
                    title="No skill data yet"
                    description="Once scrapers and saved searches have data, the skill pulse will appear here."
                  />
                )}
              </div>
            </Surface>
          </div>
        }
        secondary={
          <div className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-1">
              <SideStat
                label="Interviews"
                value={loadingOverview ? "..." : summary.total_interviews.toLocaleString()}
                hint="Conversations already moving beyond first response."
                icon={<TrendUp size={18} weight="bold" className="text-accent-success" />}
                tone="success"
              />
              <SideStat
                label="Offers"
                value={loadingOverview ? "..." : summary.total_offers.toLocaleString()}
                hint="Late-stage outcomes currently on the board."
                icon={<DownloadSimple size={18} weight="bold" className="text-accent-warning" />}
                tone="warning"
              />
            </div>

            <Surface tone="default" padding="lg" radius="xl">
              <SectionHeader
                title="Source quality"
                description="Live source quality and matching ratios for connected feeds."
              />

              {sources && sources.length ? (
                <div className="mt-4 overflow-x-auto">
                  <table className="min-w-full border-separate border-spacing-0">
                    <thead>
                      <tr className="text-left text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
                        <th className="border-b-2 border-border py-3 pr-3">Source</th>
                        <th className="border-b-2 border-border px-3 py-3 text-right">Jobs</th>
                        <th className="border-b-2 border-border px-3 py-3 text-right">Quality</th>
                        <th className="border-b-2 border-border pl-3 py-3 text-right">Match</th>
                      </tr>
                    </thead>
                    <tbody>
                      {sources.map((source) => (
                        <tr key={source.source} className="align-top">
                          <td className="border-b-2 border-border py-4 pr-3 text-sm font-bold uppercase tracking-[-0.03em] text-text-primary">
                            {source.source}
                          </td>
                          <td className="border-b-2 border-border px-3 py-4 text-right font-mono text-sm text-text-primary">
                            {source.total_jobs}
                          </td>
                          <td className="border-b-2 border-border px-3 py-4 text-right font-mono text-sm">
                            <span
                              className={cn(
                                source.quality_score >= 0.8
                                  ? "text-accent-success"
                                  : source.quality_score >= 0.5
                                    ? "text-accent-warning"
                                    : "text-accent-danger"
                              )}
                            >
                              {(source.quality_score * 100).toFixed(0)}%
                            </span>
                          </td>
                          <td className="border-b-2 border-border pl-3 py-4 text-right font-mono text-sm text-text-primary">
                            {source.avg_match_score ? `${(source.avg_match_score * 100).toFixed(0)}%` : "—"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="mt-4">
                  <EmptyState
                    icon={<Briefcase size={34} weight="bold" />}
                    title="No source quality yet"
                    description="Once scrapers and saved searches have data, the quality table will appear here."
                  />
                </div>
              )}
            </Surface>

            <StateBlock
              tone="neutral"
              icon={<TrendUp size={18} weight="bold" />}
              title="Live feed"
              description="This page stays coupled to the live analytics contract so charts and feed quality remain accurate."
            />
          </div>
        }
      />
    </div>
  );
}
