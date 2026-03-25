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
import { analyticsApi } from "../api/analytics";
import Skeleton from "../components/ui/Skeleton";
import { cn } from "../lib/utils";
import { motion } from "framer-motion";

const Charts = lazy(() => import("../components/analytics/AnalyticsCharts"));
const ANALYTICS_STALE_TIME = 10 * 60 * 1000;

const HERO_PANEL =
  "border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-secondary)] shadow-[4px_4px_0px_0px_var(--color-text-primary)]";
const INSET_PANEL =
  "border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-tertiary)] shadow-[4px_4px_0px_0px_var(--color-text-primary)]";
const CHIP =
  "inline-flex items-center gap-1 border-2 border-[var(--color-text-primary)] px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.18em]";

function ChartsSkeleton() {
  return (
    <div className="grid gap-4 lg:grid-cols-2">
      {Array.from({ length: 4 }).map((_, index) => (
        <div key={index} className={cn(HERO_PANEL, "p-4")}>
          <Skeleton variant="text" className="mb-4 h-4 w-1/3" />
          <Skeleton variant="rect" className="h-64 w-full" />
        </div>
      ))}
    </div>
  );
}

function MetricTile({
  label,
  value,
  hint,
  icon,
  tone,
}: {
  label: string;
  value: string;
  hint: string;
  icon: ReactNode;
  tone: string;
}) {
  return (
    <div className={cn("border-2 border-[var(--color-text-primary)] p-4 shadow-[4px_4px_0px_0px_var(--color-text-primary)]", tone)}>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-text-muted">
            {label}
          </div>
          <div className="mt-3 text-3xl font-semibold tracking-[-0.05em] text-text-primary">
            {value}
          </div>
          <p className="mt-2 text-sm leading-6 text-text-secondary">{hint}</p>
        </div>
        <div className="flex size-10 shrink-0 items-center justify-center border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-secondary)]">
          {icon}
        </div>
      </div>
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
      value: loadingOverview ? "..." : summary.total_jobs.toLocaleString(),
      hint: "Known opportunities in the workspace.",
      icon: <Briefcase size={18} weight="bold" />,
    tone: "bg-bg-secondary",
    },
    {
      key: "applications",
      label: "Applications",
      value: loadingOverview ? "..." : summary.total_applications.toLocaleString(),
      hint: "Applications tracked from search to outcome.",
      icon: <PaperPlaneTilt size={18} weight="bold" />,
      tone: "bg-accent-primary/8",
    },
    {
      key: "responses",
      label: "Response rate",
      value: loadingOverview ? "..." : `${Math.round(summary.response_rate * 100)}%`,
      hint: "How often the market answers back.",
      icon: <TrendUp size={18} weight="bold" />,
      tone: "bg-accent-success/8",
    },
    {
      key: "latency",
      label: "Avg days to response",
      value: loadingOverview ? "..." : summary.avg_days_to_response.toFixed(1),
      hint: "Average time from application to a meaningful reply.",
      icon: <Clock size={18} weight="bold" />,
      tone: "bg-accent-warning/8",
    },
  ];

  return (
    <div className="space-y-6 px-4 py-4 sm:px-6 sm:py-6">
      <motion.section
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
        className={cn(HERO_PANEL, "overflow-hidden")}
      >
        <div className="grid gap-0 xl:grid-cols-[minmax(0,1.4fr)_minmax(320px,0.8fr)]">
          <div className="p-5 sm:p-6 lg:p-8">
            <div className="flex flex-wrap items-center gap-2">
              <span className={CHIP}>Intelligence</span>
              <span className={CHIP}>Last 30 days</span>
            </div>
            <h1 className="mt-4 text-4xl font-semibold tracking-[-0.06em] sm:text-5xl lg:text-6xl">
              Analytics
            </h1>
            <p className="mt-4 max-w-2xl text-sm leading-6 text-text-secondary sm:text-base">
              A dense, readable control surface for understanding discovery volume, applications,
              response quality, and source health.
            </p>

            <div className="mt-6 flex flex-wrap gap-3">
                <button className={cn(CHIP, "bg-bg-secondary text-text-primary")}>
                Last 30 Days
              </button>
                <button className={cn(CHIP, "bg-accent-success/10 text-text-primary")}>
                <DownloadSimple size={12} weight="bold" />
                Export PDF
              </button>
            </div>
          </div>

          <div className="border-t-2 border-[var(--color-text-primary)] bg-[var(--color-bg-tertiary)] p-5 sm:p-6 xl:border-l-2 xl:border-t-0">
            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
              <MetricTile
                label="Interviews"
                value={loadingOverview ? "..." : summary.total_interviews.toLocaleString()}
                hint="Conversations already moving beyond first response."
                icon={<TrendUp size={18} weight="bold" />}
                tone="bg-accent-success/8"
              />
              <MetricTile
                label="Offers"
                value={loadingOverview ? "..." : summary.total_offers.toLocaleString()}
                hint="Late-stage outcomes currently on the board."
                icon={<DownloadSimple size={18} weight="bold" />}
                tone="bg-accent-warning/8"
              />
            </div>
          </div>
        </div>
      </motion.section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {metrics.map((metric) => (
          <MetricTile
            key={metric.key}
            label={metric.label}
            value={metric.value}
            hint={metric.hint}
            icon={metric.icon}
            tone={metric.tone}
          />
        ))}
      </section>

      <section className="grid gap-4 xl:grid-cols-[minmax(0,1.45fr)_minmax(340px,0.8fr)]">
        <div className="space-y-4">
          <div className={cn(HERO_PANEL, "overflow-hidden")}>
            <div className="border-b-2 border-[var(--color-text-primary)] bg-[var(--color-bg-tertiary)] px-5 py-4 sm:px-6">
              <div className="flex flex-wrap items-end justify-between gap-3">
                <div>
                  <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-text-muted">
                    Trend and funnel views
                  </div>
                  <h2 className="mt-1 text-xl font-semibold uppercase tracking-[-0.04em] sm:text-2xl">
                    Chart slab
                  </h2>
                </div>
                <span className={CHIP}>Lazy loaded</span>
              </div>
            </div>

            <div className="p-4 sm:p-5">
              <Suspense fallback={<ChartsSkeleton />}>
                <Charts daily={daily} funnel={funnel} sources={sources} skills={skills} />
              </Suspense>
            </div>
          </div>

          <div className={cn(INSET_PANEL, "p-5 sm:p-6")}>
            <div className="flex items-center justify-between gap-3">
              <div>
                <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-text-muted">
                  Top skills requested
                </div>
                <h3 className="mt-1 text-lg font-semibold uppercase tracking-[-0.04em]">
                  Skills pulse
                </h3>
              </div>
              <span className={CHIP}>{skills?.length ?? 0}</span>
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              {skills?.length ? (
                skills.slice(0, 8).map((skill) => (
                  <span
                    key={skill.skill}
                    className="border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-secondary)] px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.18em]"
                  >
                    {skill.skill}
                  </span>
                ))
              ) : (
                <span className="text-sm text-text-secondary">
                  No skill data yet.
                </span>
              )}
            </div>
          </div>
        </div>

        <div className={cn(HERO_PANEL, "overflow-hidden")}>
          <div className="border-b-2 border-[var(--color-text-primary)] bg-[var(--color-bg-tertiary)] px-5 py-4 sm:px-6">
            <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-text-muted">
              Source quality
            </div>
            <h2 className="mt-1 text-xl font-semibold uppercase tracking-[-0.04em] sm:text-2xl">
              Live feed
            </h2>
          </div>

          {sources && sources.length ? (
            <div className="overflow-x-auto p-4 sm:p-5">
              <table className="min-w-full border-separate border-spacing-0">
                <thead>
                  <tr className="text-left text-[10px] uppercase tracking-[0.18em] text-text-muted">
                    <th className="border-b-2 border-[var(--color-text-primary)] py-3 pr-3">Source</th>
                    <th className="border-b-2 border-[var(--color-text-primary)] px-3 py-3 text-right">Jobs</th>
                    <th className="border-b-2 border-[var(--color-text-primary)] px-3 py-3 text-right">Quality</th>
                    <th className="border-b-2 border-[var(--color-text-primary)] pl-3 py-3 text-right">Match</th>
                  </tr>
                </thead>
                <tbody>
                  {sources.map((source) => (
                    <tr key={source.source} className="align-top">
                      <td className="border-b-2 border-[var(--color-text-primary)] py-4 pr-3 text-sm font-semibold uppercase tracking-[-0.03em] text-text-primary">
                        {source.source}
                      </td>
                      <td className="border-b-2 border-[var(--color-text-primary)] px-3 py-4 text-right font-mono text-sm text-text-primary">
                        {source.total_jobs}
                      </td>
                      <td className="border-b-2 border-[var(--color-text-primary)] px-3 py-4 text-right font-mono text-sm">
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
                      <td className="border-b-2 border-[var(--color-text-primary)] pl-3 py-4 text-right font-mono text-sm text-text-primary">
                        {source.avg_match_score ? `${(source.avg_match_score * 100).toFixed(0)}%` : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="p-5 sm:p-6">
              <div className="border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-tertiary)] p-5">
                <div className="text-sm font-semibold uppercase tracking-[0.18em] text-text-muted">
                  No source quality yet
                </div>
                <p className="mt-3 text-sm leading-6 text-text-secondary">
                  Once scrapers and saved searches have data, the quality table will appear here.
                </p>
              </div>
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
