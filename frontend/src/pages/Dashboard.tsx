import { Briefcase, PaperPlaneTilt, TrendUp, UsersThree } from "@phosphor-icons/react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { analyticsApi, type AnalyticsOverview } from "../api/analytics";
import { jobsApi } from "../api/jobs";
import { pipelineApi } from "../api/pipeline";
import { MetricStrip } from "../components/system/MetricStrip";
import { PageHeader } from "../components/system/PageHeader";
import { SplitWorkspace } from "../components/system/SplitWorkspace";
import Badge from "../components/ui/Badge";
import {
  DashboardHeaderActions,
  JobFeedPanel,
  NextActionsPanel,
  PipelineSummaryPanel,
} from "../components/dashboard/DashboardPanels";
import {
  DEFAULT_OVERVIEW,
  DASHBOARD_METRIC_SPECS,
  PIPELINE_STAGES,
} from "../components/dashboard/DashboardData";

const METRIC_ICONS = {
  jobs: <Briefcase size={18} weight="bold" />,
  applications: <PaperPlaneTilt size={18} weight="bold" />,
  interviews: <UsersThree size={18} weight="bold" />,
  offers: <TrendUp size={18} weight="bold" />,
} as const;

export default function Dashboard() {
  const navigate = useNavigate();

  const { data: overview, isLoading: loadingOverview } = useQuery({
    queryKey: ["analytics", "overview"],
    queryFn: () => analyticsApi.overview().then((r) => r.data),
  });

  const { data: recentJobs, isLoading: loadingJobs } = useQuery({
    queryKey: ["jobs", "recent"],
    queryFn: () =>
      jobsApi.list({ page_size: 5, sort_by: "scraped_at", sort_order: "desc" }).then((r) => r.data),
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
      >
        <PageHeader
          eyebrow="Home"
          title="Command Center"
          description="Job feed, pipeline, and next actions."
          meta={
            <>
              <Badge variant="info">{stats.jobs_scraped_today.toLocaleString()} scraped today</Badge>
              <Badge variant="secondary">{Math.round(stats.response_rate * 100)}% response rate</Badge>
            </>
          }
          actions={
            <DashboardHeaderActions
              onBrowseJobs={() => navigate("/jobs")}
              onAddApplication={() => navigate("/pipeline")}
            />
          }
        />
      </motion.section>

      <MetricStrip
        items={DASHBOARD_METRIC_SPECS.map((metric) => ({
          key: metric.key,
          label: metric.label,
          value:
            metric.key === "jobs"
              ? loadingOverview
                ? "..."
                : stats.total_jobs.toLocaleString()
              : metric.key === "applications"
                ? loadingOverview
                  ? "..."
                  : stats.total_applications.toLocaleString()
                : metric.key === "interviews"
                  ? loadingOverview
                    ? "..."
                    : stats.total_interviews.toLocaleString()
                  : loadingOverview
                    ? "..."
                    : stats.total_offers.toLocaleString(),
          hint: metric.hint,
          tone: metric.tone,
          icon: METRIC_ICONS[metric.key as keyof typeof METRIC_ICONS],
        }))}
        className="xl:grid-cols-4"
      />

      <SplitWorkspace
        primary={
          <div className="space-y-4">
            <PipelineSummaryPanel
              totalApps={totalApps}
              lateStageCount={lateStageCount}
              totalOffers={stats.total_offers}
            />
            <JobFeedPanel jobs={recentJobs?.items} loadingJobs={loadingJobs} />
          </div>
        }
        secondary={<NextActionsPanel lateStageCount={lateStageCount} firstJob={firstJob} />}
      />
    </div>
  );
}
