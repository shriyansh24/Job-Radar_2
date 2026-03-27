import {
  ArrowRight,
  Briefcase,
  Buildings,
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
import Badge from "../components/ui/Badge";
import Button from "../components/ui/Button";
import {
  MetricStrip,
  PageHeader,
  SplitWorkspace,
  StateBlock,
  Surface,
} from "../components/system";

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

const PIPELINE_STAGES = [
  { key: "saved", label: "Saved" },
  { key: "applied", label: "Applied" },
  { key: "screening", label: "Screening" },
  { key: "interviewing", label: "Interviewing" },
  { key: "offer", label: "Offer" },
  { key: "accepted", label: "Accepted" },
];

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
    <Surface tone="subtle" padding="md" className="transition-transform duration-150 hover:-translate-y-0.5">
      <div className="flex items-start gap-4">
        <div className="flex size-11 shrink-0 items-center justify-center border-2 border-border bg-background text-muted-foreground shadow-[var(--shadow-xs)]">
          {icon}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-start justify-between gap-2">
            <h3 className="text-sm font-semibold uppercase tracking-[-0.03em] text-foreground sm:text-base">
              {title}
            </h3>
            {badge ? <Badge variant="outline">{badge}</Badge> : null}
          </div>
          <p className="mt-2 text-sm leading-6 text-muted-foreground">{meta}</p>
        </div>
      </div>
    </Surface>
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

  const metricItems = [
    {
      key: "jobs",
      label: "Total jobs",
      value: loadingOverview ? "..." : stats.total_jobs.toLocaleString(),
      icon: <Briefcase size={18} weight="bold" />,
      tone: "default" as const,
      hint: "Jobs in the current feed.",
    },
    {
      key: "applications",
      label: "Applications",
      value: loadingOverview ? "..." : stats.total_applications.toLocaleString(),
      icon: <PaperPlaneTilt size={18} weight="bold" />,
      tone: "default" as const,
      hint: "Tracked applications in motion.",
    },
    {
      key: "interviews",
      label: "Interviews",
      value: loadingOverview ? "..." : stats.total_interviews.toLocaleString(),
      icon: <UsersThree size={18} weight="bold" />,
      tone: "warning" as const,
      hint: "Late-stage conversations.",
    },
    {
      key: "offers",
      label: "Offers",
      value: loadingOverview ? "..." : stats.total_offers.toLocaleString(),
      icon: <TrendUp size={18} weight="bold" />,
      tone: "success" as const,
      hint: "Signals ready to close.",
    },
  ];

  return (
    <div className="space-y-6 px-4 py-4 sm:px-6 sm:py-6">
      <motion.section
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
      >
        <PageHeader
          eyebrow="Home"
          title="Command Center"
          description="Watch the live job stream, pressure map, and queue status from a single operating surface."
          meta={
            <>
              <Badge variant="info">{stats.jobs_scraped_today.toLocaleString()} scraped today</Badge>
              <Badge variant="secondary">{Math.round(stats.response_rate * 100)}% response rate</Badge>
            </>
          }
          actions={
            <>
              <Button
                variant="primary"
                icon={<ArrowRight size={16} weight="bold" />}
                onClick={() => navigate("/jobs")}
              >
                Browse jobs
              </Button>
              <Button
                variant="secondary"
                icon={<Plus size={16} weight="bold" />}
                onClick={() => navigate("/pipeline")}
              >
                Add application
              </Button>
              <Button
                variant="secondary"
                icon={<Sparkle size={16} weight="bold" />}
                onClick={() => navigate("/copilot")}
              >
                Open copilot
              </Button>
            </>
          }
        />
      </motion.section>

      <MetricStrip items={metricItems} className="xl:grid-cols-4" />

      <SplitWorkspace
        primary={
          <div className="space-y-4">
            <Surface tone="default" padding="none" className="overflow-hidden">
              <div className="flex flex-wrap items-end justify-between gap-4 border-b-2 border-border bg-[var(--color-bg-tertiary)] px-5 py-4 sm:px-6">
                <div>
                  <div className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-text-muted">
                    Pipeline distribution
                  </div>
                  <h2 className="mt-1 font-display text-xl font-black uppercase tracking-[-0.05em] text-foreground sm:text-2xl">
                    Pressure map
                  </h2>
                </div>
                <div className="flex flex-wrap gap-2">
                  <Badge variant="secondary">Applied</Badge>
                  <Badge variant="secondary">Interview</Badge>
                  <Badge variant="secondary">Offer</Badge>
                </div>
              </div>

              <div className="space-y-5 p-5 sm:p-6">
                <div className="relative h-12 overflow-hidden border-2 border-border bg-background">
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
                  <StateBlock
                    tone="muted"
                    title="Volume low"
                    description={`${Math.max(totalApps - lateStageCount, 0)} leads still in the top of the funnel.`}
                  />
                  <StateBlock
                    tone="warning"
                    title="Volume mid"
                    description={`${lateStageCount.toLocaleString()} active records are in motion.`}
                  />
                  <StateBlock
                    tone="success"
                    title="Volume high"
                    description={`${stats.total_offers.toLocaleString()} final-stage records are ready to close.`}
                  />
                </div>
              </div>
            </Surface>

            <Surface tone="default" padding="none" className="overflow-hidden">
              <div className="flex items-center justify-between gap-3 border-b-2 border-border bg-[var(--color-bg-tertiary)] px-5 py-4 sm:px-6">
                <div>
                  <div className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-text-muted">
                    Transmission feed
                  </div>
                  <h2 className="mt-1 font-display text-xl font-black uppercase tracking-[-0.05em] text-foreground">
                    Recent movement
                  </h2>
                </div>
                <Badge variant="info">Live</Badge>
              </div>

              <div className="space-y-3 p-5 sm:p-6">
                {loadingJobs ? (
                  <div className="space-y-3">
                    {Array.from({ length: 3 }).map((_, index) => (
                      <div
                        key={index}
                        className="h-20 animate-pulse border-2 border-border bg-[var(--color-bg-tertiary)]"
                      />
                    ))}
                  </div>
                ) : recentJobs?.items.length ? (
                  recentJobs.items.map((job, index) => (
                    <FeedRow
                      key={job.id}
                      title={`${job.title}${job.company_name ? ` @ ${job.company_name}` : ""}`}
                      meta={[
                        job.location,
                        job.remote_type,
                        job.posted_at
                          ? formatDistanceToNow(new Date(job.posted_at), { addSuffix: true })
                          : null,
                      ]
                        .filter(Boolean)
                        .join(" • ")}
                      badge={
                        job.match_score !== null
                          ? `${Math.round(job.match_score * 100)}% match`
                          : undefined
                      }
                      icon={
                        index === 0 ? (
                          <PaperPlaneTilt size={18} weight="bold" />
                        ) : (
                          <Buildings size={18} weight="bold" />
                        )
                      }
                    />
                  ))
                ) : (
                  <StateBlock
                    tone="muted"
                    title="No recent jobs yet"
                    description="Once the scraper fills the board, the newest posting appears here as a one-tap action."
                  />
                )}
              </div>
            </Surface>
          </div>
        }
        secondary={
          <div className="space-y-4">
            <Surface tone="default" padding="none" className="overflow-hidden">
              <div className="flex items-end justify-between gap-4 border-b-2 border-border bg-[var(--color-bg-tertiary)] px-5 py-4 sm:px-6">
                <div>
                  <div className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-text-muted">
                    Immediate actions
                  </div>
                  <h2 className="mt-1 font-display text-xl font-black uppercase tracking-[-0.05em] text-foreground sm:text-2xl">
                    Priority queue
                  </h2>
                </div>
                <Sparkle size={18} weight="fill" className="text-[var(--color-accent-primary)]" />
              </div>

              <div className="space-y-3 p-5 sm:p-6">
                <StateBlock
                  tone={lateStageCount > 0 ? "warning" : "muted"}
                  title={
                    lateStageCount > 0
                      ? `${lateStageCount} late-stage applications`
                      : "No late-stage applications"
                  }
                  description={
                    lateStageCount > 0
                      ? "Follow up on interview and offer records before the queue cools."
                      : "Push more roles into the board to surface follow-up work here."
                  }
                  action={
                    <Badge variant={lateStageCount > 0 ? "warning" : "secondary"}>
                      {lateStageCount > 0 ? "Urgent" : "Idle"}
                    </Badge>
                  }
                />
                <StateBlock
                  tone={firstJob ? "warning" : "muted"}
                  title={
                    firstJob
                      ? `Review the newest posting${firstJob.company_name ? ` from ${firstJob.company_name}` : ""}`
                      : "No posting to review"
                  }
                  description={
                    firstJob
                      ? `${firstJob.title}${firstJob.location ? ` • ${firstJob.location}` : ""}`
                      : "Once jobs land, the latest posting becomes a one-tap action."
                  }
                  action={<Badge variant={firstJob ? "info" : "secondary"}>{firstJob ? "New" : "Empty"}</Badge>}
                />
                <StateBlock
                  tone="muted"
                  title="Queue clear"
                  description="No further actions are pending right now."
                />
              </div>
            </Surface>
          </div>
        }
      />
    </div>
  );
}
