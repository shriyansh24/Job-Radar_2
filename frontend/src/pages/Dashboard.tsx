import {
  ArrowRight,
  Briefcase,
  Buildings,
  Clock,
  PaperPlaneTilt,
  Plus,
  Sparkle,
  TrendUp,
  UsersThree,
} from "@phosphor-icons/react";
import { useQuery } from "@tanstack/react-query";
import { formatDistanceToNow } from "date-fns";
import { motion } from "framer-motion";
import type { ReactNode } from "react";
import { useNavigate } from "react-router-dom";
import { analyticsApi, type AnalyticsOverview } from "../api/analytics";
import { jobsApi } from "../api/jobs";
import { pipelineApi } from "../api/pipeline";
import Button from "../components/ui/Button";
import { cn } from "../lib/utils";

const HERO_PANEL =
  "border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-secondary)]";
const INSET_PANEL =
  "border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-tertiary)]";
const CHIP =
  "inline-flex items-center gap-1 border-2 border-[var(--color-text-primary)] px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.18em]";
const BUTTON_BASE =
  "!rounded-none !border-2 !border-[var(--color-text-primary)] !uppercase !tracking-[0.18em]";

const PIPELINE_STAGES = [
  { key: "saved", label: "Saved", color: "bg-text-muted" },
  { key: "applied", label: "Applied", color: "bg-accent-primary" },
  { key: "screening", label: "Screening", color: "bg-accent-primary/70" },
  { key: "interviewing", label: "Interviewing", color: "bg-accent-warning" },
  { key: "offer", label: "Offer", color: "bg-accent-success" },
  { key: "accepted", label: "Accepted", color: "bg-accent-success" },
];

const DEFAULT_OVERVIEW: AnalyticsOverview = {
  total_jobs: 0,
  total_applications: 0,
  total_interviews: 0,
  total_offers: 0,
  applications_by_status: {},
  response_rate: 0,
  avg_days_to_response: 0,
  jobs_scraped_today: 0,
  enriched_jobs: 0,
};

function HeroMetric({
  label,
  value,
  icon,
  tone = "default",
}: {
  label: string;
  value: string;
  icon: ReactNode;
  tone?: "default" | "success" | "warning" | "info";
}) {
  const toneClass = {
    default: "bg-bg-secondary",
    success: "bg-accent-success/10",
    warning: "bg-accent-warning/10",
    info: "bg-accent-primary/10",
  }[tone];

  return (
    <div className={cn(HERO_PANEL, "p-4", toneClass)}>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-text-muted">
            {label}
          </div>
          <div className="mt-2 text-3xl font-semibold tracking-[-0.05em] text-text-primary">
            {value}
          </div>
        </div>
        <div className="flex size-10 shrink-0 items-center justify-center border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-tertiary)]">
          {icon}
        </div>
      </div>
    </div>
  );
}

function FeedRow({
  title,
  meta,
  badge,
  icon,
}: {
  title: string;
  meta: string;
  badge?: string;
  icon: ReactNode;
}) {
  return (
    <div className="border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-secondary)] p-4 transition-colors hover:bg-black/5 dark:hover:bg-white/5">
      <div className="flex items-start gap-4">
        <div className="flex size-12 shrink-0 items-center justify-center border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-tertiary)]">
          {icon}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-start justify-between gap-2">
            <h3 className="text-sm font-semibold uppercase tracking-[-0.03em] text-text-primary sm:text-base">
              {title}
            </h3>
            {badge ? (
              <span className={CHIP}>{badge}</span>
            ) : null}
          </div>
          <p className="mt-2 text-sm leading-6 text-text-secondary">{meta}</p>
        </div>
      </div>
    </div>
  );
}

function MetricTile({
  label,
  value,
  icon,
  accent,
}: {
  label: string;
  value: string;
  icon: ReactNode;
  accent: string;
}) {
  return (
    <div className={cn(HERO_PANEL, "p-5", accent)}>
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-text-muted">
            {label}
          </div>
          <div className="mt-3 text-4xl font-semibold tracking-[-0.06em] text-text-primary">
            {value}
          </div>
        </div>
        <div className="flex size-11 shrink-0 items-center justify-center border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-tertiary)]">
          {icon}
        </div>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const navigate = useNavigate();

  const { data: overview, isLoading: loadingOverview } = useQuery({
    queryKey: ["analytics", "overview"],
    queryFn: () => analyticsApi.overview().then((r) => r.data),
  });

  const { data: recentJobs, isLoading: loadingJobs } = useQuery({
    queryKey: ["jobs", "recent"],
    queryFn: () =>
      jobsApi
        .list({ page_size: 5, sort_by: "scraped_at", sort_order: "desc" })
        .then((r) => r.data),
  });

  const { data: pipelineData } = useQuery({
    queryKey: ["pipeline"],
    queryFn: () => pipelineApi.pipeline().then((r) => r.data),
  });

  const stats: AnalyticsOverview = {
    ...DEFAULT_OVERVIEW,
    ...(overview ?? {}),
    applications_by_status: overview?.applications_by_status ?? {},
  };

  const pipelineCounts = PIPELINE_STAGES.map((stage) => ({
    ...stage,
    count: pipelineData?.[stage.key]?.length || 0,
  }));
  const totalApps = pipelineCounts.reduce((sum, stage) => sum + stage.count, 0);
  const lateStageCount = pipelineCounts
    .filter((stage) => ["interviewing", "offer", "accepted"].includes(stage.key))
    .reduce((sum, stage) => sum + stage.count, 0);

  const firstJob = recentJobs?.items[0];

  return (
    <div className="space-y-6 px-4 py-4 sm:px-6 sm:py-6">
      <motion.section
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
        className={cn(HERO_PANEL, "overflow-hidden")}
      >
        <div className="grid gap-0 xl:grid-cols-[minmax(0,1.45fr)_minmax(320px,0.8fr)]">
          <div className="p-5 sm:p-6 lg:p-8">
            <div className="flex flex-wrap items-center gap-2">
              <span className={CHIP}>Home</span>
              <span className={CHIP}>
                {stats.jobs_scraped_today.toLocaleString()} jobs scraped today
              </span>
            </div>
            <h1 className="mt-4 text-4xl font-semibold tracking-[-0.06em] sm:text-5xl lg:text-6xl">
              Command Center
            </h1>

            <div className="mt-6 flex flex-wrap gap-3">
              <Button
                variant="primary"
                onClick={() => navigate("/jobs")}
                icon={<ArrowRight size={16} weight="bold" />}
                className={cn(BUTTON_BASE, "bg-accent-primary text-white dark:!bg-blue-700 dark:hover:!bg-blue-800 transition-colors")}
              >
                Browse jobs
              </Button>
              <Button
                variant="secondary"
                onClick={() => navigate("/pipeline")}
                icon={<Plus size={16} weight="bold" />}
                className={cn(BUTTON_BASE, "bg-bg-secondary text-text-primary transition-colors hover:bg-black/5 dark:hover:bg-white/5")}
              >
                Add application
              </Button>
              <Button
                variant="secondary"
                onClick={() => navigate("/copilot")}
                icon={<Sparkle size={16} weight="bold" />}
                className={cn(BUTTON_BASE, "bg-bg-secondary text-text-primary transition-colors hover:bg-black/5 dark:hover:bg-white/5")}
              >
                Open copilot
              </Button>
            </div>
          </div>

          <div className="border-t-2 border-[var(--color-text-primary)] bg-[var(--color-bg-tertiary)] p-5 sm:p-6 xl:border-l-2 xl:border-t-0">
            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
              <HeroMetric
                label="Global success rate"
                value={`${Math.round(stats.response_rate * 100)}%`}
                icon={<TrendUp size={18} weight="bold" />}
                tone="success"
              />
              <HeroMetric
                label="Avg response time"
                value={`${stats.avg_days_to_response.toFixed(1)}d`}
                icon={<Clock size={18} weight="bold" />}
                tone="info"
              />
            </div>
          </div>
        </div>
      </motion.section>

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricTile
          label="Total jobs"
          value={loadingOverview ? "..." : stats.total_jobs.toLocaleString()}
          icon={<Briefcase size={18} weight="bold" />}
          accent="bg-accent-primary/8"
        />
        <MetricTile
          label="Applications"
          value={loadingOverview ? "..." : stats.total_applications.toLocaleString()}
          icon={<PaperPlaneTilt size={18} weight="bold" />}
          accent="bg-accent-primary/8"
        />
        <MetricTile
          label="Interviews"
          value={loadingOverview ? "..." : stats.total_interviews.toLocaleString()}
          icon={<UsersThree size={18} weight="bold" />}
          accent="bg-accent-warning/8"
        />
        <MetricTile
          label="Offers"
          value={loadingOverview ? "..." : stats.total_offers.toLocaleString()}
          icon={<TrendUp size={18} weight="bold" />}
          accent="bg-accent-success/8"
        />
      </section>

      <section className="grid gap-4 lg:grid-cols-[minmax(0,1.2fr)_minmax(320px,0.8fr)] xl:grid-cols-[minmax(0,1.5fr)_minmax(320px,0.8fr)]">
        <div className="space-y-4">
          <div className={cn(INSET_PANEL, "p-5 sm:p-6")}>
            <div className="flex flex-wrap items-end justify-between gap-4">
              <div>
                <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-text-muted">
                  Pipeline distribution
                </div>
                <h2 className="mt-2 text-xl font-semibold uppercase tracking-[-0.04em] sm:text-2xl">
                  Pressure map
                </h2>
              </div>
              <div className="flex flex-wrap gap-2 text-[10px] font-semibold uppercase tracking-[0.18em]">
                <span className={CHIP}>Applied</span>
                <span className={CHIP}>Interview</span>
                <span className={CHIP}>Offer</span>
              </div>
            </div>

            <div className="mt-6 space-y-5">
              <div className="relative h-12 border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-secondary)]">
                <motion.div
                  className="h-full bg-[var(--color-text-primary)]"
                  initial={{ width: 0 }}
                  animate={{ width: totalApps > 0 ? "55%" : "0%" }}
                  transition={{ type: "spring", stiffness: 180, damping: 24 }}
                />
                <motion.div
                  className="h-full bg-[var(--color-accent-primary)]"
                  initial={{ width: 0 }}
                  animate={{ width: totalApps > 0 ? "30%" : "0%" }}
                  transition={{ type: "spring", stiffness: 180, damping: 24, delay: 0.05 }}
                />
                <motion.div
                  className="h-full bg-[var(--color-accent-success)]"
                  initial={{ width: 0 }}
                  animate={{ width: totalApps > 0 ? "15%" : "0%" }}
                  transition={{ type: "spring", stiffness: 180, damping: 24, delay: 0.1 }}
                />
              </div>

              <div className="grid gap-3 sm:grid-cols-3">
                {[
                  {
                    label: "Volume low",
                    value: Math.max(totalApps - lateStageCount, 0),
                    hint: "leads",
                    tone: "bg-bg-secondary",
                  },
                  {
                    label: "Volume mid",
                    value: lateStageCount,
                    hint: "active",
                    tone: "bg-accent-primary/8",
                  },
                  {
                    label: "Volume high",
                    value: stats.total_offers,
                    hint: "final",
                    tone: "bg-accent-success/8",
                  },
                ].map((item) => (
                  <div key={item.label} className={cn("border-2 border-[var(--color-text-primary)] p-4", item.tone)}>
                    <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-text-muted">
                      {item.label}
                    </div>
                    <div className="mt-3 flex items-baseline gap-2">
                      <span className="text-2xl font-semibold tracking-[-0.05em]">{item.value}</span>
                      <span className="text-[10px] font-semibold uppercase tracking-[0.18em] text-text-muted">
                        {item.hint}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className={cn(HERO_PANEL, "overflow-hidden")}>
            <div className="flex items-center justify-between gap-3 border-b-2 border-[var(--color-text-primary)] bg-[var(--color-bg-tertiary)] px-5 py-4 sm:px-6">
              <div>
                <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-text-muted">
                  Transmission feed
                </div>
                <h2 className="mt-1 text-xl font-semibold uppercase tracking-[-0.04em]">
                  Recent movement
                </h2>
              </div>
              <span className={CHIP}>Live</span>
            </div>

            <div className="divide-y-2 divide-[var(--color-text-primary)]">
              {loadingJobs ? (
                <div className="space-y-3 p-5 sm:p-6">
                  {Array.from({ length: 3 }).map((_, index) => (
                    <div
                      key={index}
                      className="h-20 animate-pulse border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-tertiary)]"
                    />
                  ))}
                </div>
              ) : recentJobs?.items.length ? (
                recentJobs.items.map((job, index) => (
                  <div key={job.id} className="p-5 sm:p-6">
                    <FeedRow
                      title={`${job.title}${job.company_name ? ` @ ${job.company_name}` : ""}`}
                      meta={[
                        job.location,
                        job.remote_type,
                        job.posted_at
                          ? formatDistanceToNow(new Date(job.posted_at), { addSuffix: true })
                          : null,
                      ]
                        .filter(Boolean)
                        .join("  •  ")}
                      badge={job.match_score !== null ? `${Math.round(job.match_score * 100)}% MATCH` : undefined}
                      icon={index === 0 ? <PaperPlaneTilt size={18} weight="bold" /> : <Buildings size={18} weight="bold" />}
                    />
                  </div>
                ))
              ) : (
                <div className="p-5 sm:p-6">
                  <div className={cn("border-2 border-dashed border-[var(--color-text-primary)] p-5 text-sm italic", "text-text-muted")}>
                    No recent jobs yet.
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <div className={cn(HERO_PANEL, "p-5 sm:p-6")}>
            <div className="flex items-end justify-between gap-4">
              <div>
                <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-text-muted">
                  Immediate actions
                </div>
                <h2 className="mt-2 text-xl font-semibold uppercase tracking-[-0.04em] sm:text-2xl">
                  Priority queue
                </h2>
              </div>
              <Sparkle size={18} weight="fill" className="text-accent-primary" />
            </div>

            <div className="mt-5 space-y-3">
              <FeedRow
                title={
                  lateStageCount > 0
                    ? `${lateStageCount} applications in late-stage review`
                    : "No late-stage applications"
                }
                meta={
                  lateStageCount > 0
                    ? "Follow up on interview and offer stage records before the queue cools."
                    : "Push more roles into the board to surface follow-up work here."
                }
                badge={lateStageCount > 0 ? "Urgent" : "Idle"}
                icon={<Clock size={18} weight="bold" />}
              />
              <FeedRow
                title={firstJob ? `Review the newest posting${firstJob.company_name ? ` from ${firstJob.company_name}` : ""}` : "No posting to review"}
                meta={
                  firstJob
                    ? `${firstJob.title}${firstJob.location ? ` • ${firstJob.location}` : ""}`
                    : "Once jobs land, the latest posting becomes a one-tap action."
                }
                badge={firstJob ? "New" : "Empty"}
                icon={<Briefcase size={18} weight="bold" />}
              />
              <div className="border-2 border-dashed border-[var(--color-text-primary)] p-5 text-sm italic text-text-muted">
                No further actions pending.
              </div>
            </div>
          </div>

        </div>
      </section>
    </div>
  );
}
