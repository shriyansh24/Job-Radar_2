import {
  ArrowRight,
  Briefcase,
  Buildings,
  Clock,
  PaperPlaneTilt,
  Play,
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
import { jobsApi, type Job } from "../api/jobs";
import { pipelineApi } from "../api/pipeline";
import Badge from "../components/ui/Badge";
import Button from "../components/ui/Button";
import { PageHeader, SectionHeader, SplitWorkspace, StateBlock, Surface } from "../components/system";
import { cn } from "../lib/utils";

const PIPELINE_STAGES = [
  { key: "saved", label: "Saved", color: "bg-text-muted" },
  { key: "applied", label: "Applied", color: "bg-accent-primary" },
  { key: "screening", label: "Screening", color: "bg-accent-primary/60" },
  { key: "interviewing", label: "Interview", color: "bg-accent-warning" },
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

function MetricTile({
  label,
  value,
  hint,
  icon,
  accent,
}: {
  label: string;
  value: string;
  hint: string;
  icon: ReactNode;
  accent: "blue" | "green" | "amber" | "violet";
}) {
  const accentClasses = {
    blue: "border-accent-primary/20 bg-accent-primary/8",
    green: "border-accent-success/20 bg-accent-success/8",
    amber: "border-accent-warning/20 bg-accent-warning/8",
    violet: "border-accent-secondary/20 bg-accent-secondary/8",
  };

  return (
    <Surface
      tone="subtle"
      radius="xl"
      padding="md"
      className={cn("border shadow-none", accentClasses[accent])}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="text-[11px] font-medium uppercase tracking-[0.18em] text-text-muted">
            {label}
          </div>
          <div className="mt-2 text-3xl font-semibold tracking-[-0.04em] text-text-primary">
            {value}
          </div>
          <p className="mt-2 text-sm leading-6 text-text-secondary">{hint}</p>
        </div>
        <div className="flex size-10 shrink-0 items-center justify-center rounded-[var(--radius-lg)] border border-border bg-bg-secondary text-text-muted">
          {icon}
        </div>
      </div>
    </Surface>
  );
}

function RecentJobRow({ job, onClick }: { job: Job; onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="flex w-full items-center gap-4 rounded-[var(--radius-lg)] border border-transparent px-3 py-3 text-left transition-colors hover:border-border hover:bg-bg-hover"
    >
      <div className="min-w-0 flex-1">
        <div className="truncate text-sm font-medium text-text-primary">{job.title}</div>
        <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-text-muted">
          {job.company_name ? (
            <span className="inline-flex items-center gap-1">
              <Buildings size={12} weight="bold" />
              {job.company_name}
            </span>
          ) : null}
          {job.location ? (
            <span className="inline-flex items-center gap-1">
              <Clock size={12} weight="bold" />
              {job.location}
            </span>
          ) : null}
        </div>
      </div>
      <div className="flex shrink-0 items-center gap-2">
        {job.match_score !== null ? (
          <Badge
            variant={
              job.match_score >= 0.8
                ? "success"
                : job.match_score >= 0.5
                  ? "warning"
                  : "danger"
            }
            size="sm"
          >
            {Math.round(job.match_score * 100)}%
          </Badge>
        ) : null}
        {job.posted_at ? (
          <span className="text-xs text-text-muted">
            {formatDistanceToNow(new Date(job.posted_at), { addSuffix: true })}
          </span>
        ) : null}
      </div>
    </button>
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

  return (
    <div className="space-y-6 px-4 py-4 sm:px-6 sm:py-6">
      <PageHeader
        eyebrow="Home"
        title="Command Center"
        description="A compact operations view for what arrived, what moved, and what still needs attention."
        actions={
          <>
            <Button variant="secondary" onClick={() => navigate("/jobs")} icon={<Play size={16} weight="bold" />}>
              Browse jobs
            </Button>
            <Button variant="secondary" onClick={() => navigate("/pipeline")} icon={<Plus size={16} weight="bold" />}>
              Add application
            </Button>
            <Button variant="primary" onClick={() => navigate("/copilot")} icon={<Sparkle size={16} weight="bold" />}>
              Open copilot
            </Button>
          </>
        }
        meta={
          <>
            <span>{stats.jobs_scraped_today.toLocaleString()} jobs scraped today</span>
            <span>Response rate {Math.round(stats.response_rate * 100)}%</span>
            <span>{stats.total_applications.toLocaleString()} tracked applications</span>
          </>
        }
      />

      <SplitWorkspace
        primary={
          <div className="space-y-6">
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              <MetricTile
                label="Total jobs"
                value={loadingOverview ? "..." : stats.total_jobs.toLocaleString()}
                hint="Current pool of roles in the workspace."
                icon={<Briefcase size={18} weight="bold" />}
                accent="blue"
              />
              <MetricTile
                label="Applications"
                value={loadingOverview ? "..." : stats.total_applications.toLocaleString()}
                hint="Applications currently in the pipeline."
                icon={<PaperPlaneTilt size={18} weight="bold" />}
                accent="violet"
              />
              <MetricTile
                label="Interviews"
                value={loadingOverview ? "..." : stats.total_interviews.toLocaleString()}
                hint="Conversations already landed."
                icon={<UsersThree size={18} weight="bold" />}
                accent="green"
              />
              <MetricTile
                label="Offers"
                value={loadingOverview ? "..." : stats.total_offers.toLocaleString()}
                hint="The part of the funnel that matters."
                icon={<TrendUp size={18} weight="bold" />}
                accent="amber"
              />
            </div>

            <Surface tone="default" radius="xl" padding="md" className="overflow-hidden">
              <SectionHeader
                title="Recent jobs"
                description="A live feed of the newest roles. Open a row to inspect the full posting."
                action={
                  <Button variant="ghost" size="sm" onClick={() => navigate("/jobs")} icon={<ArrowRight size={14} weight="bold" />}>
                    View all
                  </Button>
                }
              />

              <div className="mt-4 divide-y divide-border">
                {loadingJobs ? (
                  <div className="space-y-3 py-2">
                    {Array.from({ length: 4 }).map((_, index) => (
                      <div key={index} className="h-14 animate-pulse rounded-[var(--radius-lg)] bg-bg-hover/60" />
                    ))}
                  </div>
                ) : recentJobs?.items.length ? (
                  recentJobs.items.map((job) => (
                    <RecentJobRow key={job.id} job={job} onClick={() => navigate("/jobs")} />
                  ))
                ) : (
                  <div className="py-8">
                    <StateBlock
                      title="No jobs yet"
                      description="Run the discovery pipeline to populate the feed."
                      tone="muted"
                      icon={<Briefcase size={18} weight="bold" />}
                      action={
                        <Button variant="secondary" size="sm" onClick={() => navigate("/jobs")}>
                          Open jobs
                        </Button>
                      }
                    />
                  </div>
                )}
              </div>
            </Surface>
          </div>
        }
        secondary={
          <div className="space-y-6">
            <Surface tone="default" radius="xl" padding="md">
              <SectionHeader
                title="Pipeline pressure"
                description="Stage distribution for the application board."
              />

              <div className="mt-5 space-y-4">
                {pipelineCounts.map((stage) => (
                  <div key={stage.key} className="space-y-2">
                    <div className="flex items-center justify-between gap-3 text-sm">
                      <span className="text-text-secondary">{stage.label}</span>
                      <span className="font-mono text-xs text-text-primary">{stage.count}</span>
                    </div>
                    <div className="h-2 overflow-hidden rounded-full bg-bg-tertiary">
                      <motion.div
                        className={cn("h-full rounded-full", stage.color)}
                        initial={{ width: 0 }}
                        animate={{
                          width: totalApps > 0 ? `${(stage.count / totalApps) * 100}%` : "0%",
                        }}
                        transition={{ type: "spring", stiffness: 180, damping: 24 }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </Surface>

            <StateBlock
              tone="neutral"
              title="Next actions"
              description="Use the command center to move into discovery, execute, or prepare without switching mental models."
              icon={<Sparkle size={18} weight="bold" />}
              action={
                <div className="flex flex-wrap gap-2">
                  <Button variant="secondary" size="sm" onClick={() => navigate("/auto-apply")}>
                    Auto apply
                  </Button>
                  <Button variant="secondary" size="sm" onClick={() => navigate("/networking")}>
                    Networking
                  </Button>
                </div>
              }
            />
          </div>
        }
      />
    </div>
  );
}
