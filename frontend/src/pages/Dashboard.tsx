import {
  ArrowRight,
  Briefcase,
  Buildings,
  Clock,
  MapPin,
  PaperPlaneTilt,
  Play,
  Plus,
  Trophy,
  UploadSimple,
  UsersThree,
} from "@phosphor-icons/react";
import { useQuery } from "@tanstack/react-query";
import { formatDistanceToNow } from "date-fns";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { analyticsApi, type AnalyticsOverview } from "../api/analytics";
import { jobsApi, type Job } from "../api/jobs";
import { pipelineApi } from "../api/pipeline";
import Badge from "../components/ui/Badge";
import Button from "../components/ui/Button";
import Card from "../components/ui/Card";
import Skeleton from "../components/ui/Skeleton";
import { cn } from "../lib/utils";

const PIPELINE_STAGES = [
  { key: "saved", label: "Saved", color: "bg-text-muted" },
  { key: "applied", label: "Applied", color: "bg-accent-primary" },
  { key: "screening", label: "Screening", color: "bg-accent-primary/60" },
  { key: "interviewing", label: "Interview", color: "bg-accent-warning" },
  { key: "offer", label: "Offer", color: "bg-accent-success" },
  { key: "accepted", label: "Accepted", color: "bg-accent-success" },
];

function RecentJobCard({ job }: { job: Job }) {
  const navigate = useNavigate();
  return (
    <button
      type="button"
      className="w-full text-left flex items-center gap-3 px-3 py-2.5 rounded-[var(--radius-md)] row-hover cursor-pointer active:translate-y-[1px]"
      onClick={() => navigate("/jobs")}
    >
      <div className="min-w-0 flex-1">
        <p className="text-sm font-medium text-text-primary truncate">
          {job.title}
        </p>
        <div className="flex items-center gap-2 text-xs text-text-muted">
          {job.company_name && (
            <span className="flex items-center gap-1">
              <Buildings size={12} weight="bold" />
              {job.company_name}
            </span>
          )}
          {job.location && (
            <span className="flex items-center gap-1">
              <MapPin size={12} weight="bold" />
              {job.location}
            </span>
          )}
        </div>
      </div>
      <div className="flex items-center gap-2 shrink-0">
        {job.match_score !== null && (
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
        )}
        {job.posted_at && (
          <span className="text-xs text-text-muted flex items-center gap-1">
            <Clock size={12} weight="bold" />
            {formatDistanceToNow(new Date(job.posted_at), { addSuffix: true })}
          </span>
        )}
      </div>
    </button>
  );
}

function KpiTile({
  label,
  value,
  icon,
  accent = "blue",
}: {
  label: string;
  value: string;
  icon: React.ReactNode;
  accent?: "blue" | "violet" | "green" | "amber";
}) {
  const accentClasses = {
    blue: "kpi-blue",
    violet: "kpi-violet",
    green: "kpi-green",
    amber: "kpi-amber",
  };
  const dotColors = {
    blue: "bg-accent-primary",
    violet: "bg-accent-secondary",
    green: "bg-accent-success",
    amber: "bg-accent-warning",
  };

  return (
    <Card className={cn("p-6 card-hover", accentClasses[accent])}>
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="label">{label}</div>
          <div className="mt-2 text-3xl font-bold text-text-primary mono-num">
            {value}
          </div>
        </div>
        <div className="shrink-0 p-2 rounded-[var(--radius-md)] bg-bg-hover text-text-muted">
          {icon}
        </div>
      </div>
      <div className="mt-4 flex items-center gap-2">
        <motion.span
          className={cn("h-1.5 w-1.5 rounded-full", dotColors[accent])}
          animate={{ opacity: [0.35, 1, 0.35] }}
          transition={{ duration: 2.2, repeat: Infinity, ease: "easeInOut" }}
        />
        <span className="text-[11px] text-text-muted">Live</span>
      </div>
    </Card>
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

  const stats: AnalyticsOverview = overview || {
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

  const pipelineCounts = PIPELINE_STAGES.map((s) => ({
    ...s,
    count: pipelineData?.[s.key]?.length || 0,
  }));
  const totalApps = pipelineCounts.reduce((sum, s) => sum + s.count, 0);

  return (
    <div className="space-y-8 animate-fade-in">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        <Card className="lg:col-span-7 p-8" hover={false}>
          <div className="flex items-start justify-between gap-6">
            <div className="min-w-0">
              <div className="label">Overview</div>
              <h1 className="mt-2 heading-xl text-text-primary">
                Dashboard
              </h1>
              <p className="mt-2 text-sm text-text-secondary max-w-[55ch] leading-relaxed">
                Track new roles, push applications forward, and keep your
                pipeline honest—without drowning in tabs.
              </p>
            </div>
          </div>

          <div className="mt-6 grid grid-cols-1 sm:grid-cols-3 gap-2.5">
            <Button
              variant="primary"
              className="justify-start"
              onClick={() => navigate("/jobs")}
              icon={<Play size={16} weight="bold" />}
            >
              Browse Jobs
            </Button>
            <Button
              variant="secondary"
              className="justify-start"
              onClick={() => navigate("/pipeline")}
              icon={<Plus size={16} weight="bold" />}
            >
              Add Application
            </Button>
            <Button
              variant="secondary"
              className="justify-start"
              onClick={() => navigate("/resume")}
              icon={<UploadSimple size={16} weight="bold" />}
            >
              Upload Resume
            </Button>
          </div>
        </Card>

        <div className="lg:col-span-5 grid grid-cols-1 sm:grid-cols-2 gap-3 stagger-children">
          {loadingOverview ? (
            Array.from({ length: 4 }).map((_, i) => (
              <div
                key={i}
                className="bg-bg-secondary border border-border rounded-[var(--radius-xl)] p-8 space-y-3"
              >
                <Skeleton variant="text" className="w-1/2 h-4" />
                <Skeleton variant="text" className="w-1/3 h-7" />
                <div className="pt-4">
                  <Skeleton variant="text" className="w-2/3 h-3" />
                </div>
              </div>
            ))
          ) : (
            <>
              <KpiTile
                label="Total Jobs"
                value={stats.total_jobs.toLocaleString()}
                icon={<Briefcase size={20} weight="bold" />}
                accent="blue"
              />
              <KpiTile
                label="Applications"
                value={stats.total_applications.toLocaleString()}
                icon={<PaperPlaneTilt size={20} weight="bold" />}
                accent="violet"
              />
              <KpiTile
                label="Interviews"
                value={stats.total_interviews.toLocaleString()}
                icon={<UsersThree size={20} weight="bold" />}
                accent="green"
              />
              <KpiTile
                label="Offers"
                value={stats.total_offers.toLocaleString()}
                icon={<Trophy size={20} weight="bold" />}
                accent="amber"
              />
            </>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        <Card className="lg:col-span-7" padding="none">
          <div className="flex items-center justify-between px-6 py-5 border-b border-border">
            <div>
              <div className="label">Stream</div>
              <h2 className="mt-1 heading-sm text-text-primary">
                Recent jobs
              </h2>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate("/jobs")}
              icon={<ArrowRight size={16} weight="bold" />}
            >
              View all
            </Button>
          </div>

          <div className="p-3">
            {loadingJobs ? (
              Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="px-3 py-3 space-y-1">
                  <Skeleton variant="text" className="w-3/4 h-4" />
                  <Skeleton variant="text" className="w-1/2 h-3" />
                </div>
              ))
            ) : recentJobs?.items.length === 0 ? (
              <div className="py-10 text-center">
                <p className="text-sm text-text-secondary">
                  No jobs yet. Run the scraper to start building your feed.
                </p>
              </div>
            ) : (
              <div className="space-y-1">
                {recentJobs?.items.map((job) => (
                  <RecentJobCard key={job.id} job={job} />
                ))}
              </div>
            )}
          </div>
        </Card>

        <Card className="lg:col-span-5 p-6">
          <div className="flex items-end justify-between gap-4">
            <div>
              <div className="label">Pipeline</div>
              <h2 className="mt-1 heading-sm text-text-primary">
                Summary
              </h2>
            </div>
            <div className="text-xs text-text-muted">
              Total:{" "}
              <span className="font-mono text-text-secondary">{totalApps}</span>
            </div>
          </div>

          <div className="mt-8 space-y-4">
            {pipelineCounts.map((stage) => (
              <div key={stage.key} className="grid grid-cols-12 gap-3 items-center">
                <span className="col-span-4 text-xs text-text-secondary">
                  {stage.label}
                </span>
                <div className="col-span-6 h-2.5 bg-bg-tertiary rounded-full overflow-hidden">
                  <motion.div
                    className={cn("h-full rounded-full", stage.color)}
                    initial={{ width: 0 }}
                    animate={{
                      width:
                        totalApps > 0 ? `${(stage.count / totalApps) * 100}%` : "0%",
                    }}
                    transition={{ type: "spring", stiffness: 180, damping: 24 }}
                  />
                </div>
                <span className="col-span-2 text-right text-xs font-medium text-text-secondary font-mono">
                  {stage.count}
                </span>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}
