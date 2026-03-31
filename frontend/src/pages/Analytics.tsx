import {
  Briefcase,
  Clock,
  PaperPlaneTilt,
  TrendUp,
} from "@phosphor-icons/react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { analyticsApi } from "../api/analytics";
import { AnalyticsPrimaryColumn } from "../components/analytics/AnalyticsPrimaryColumn";
import { AnalyticsSecondaryRail } from "../components/analytics/AnalyticsSecondaryRail";
import Badge from "../components/ui/Badge";
import { MetricStrip } from "../components/system/MetricStrip";
import { PageHeader } from "../components/system/PageHeader";
import { SplitWorkspace } from "../components/system/SplitWorkspace";
const ANALYTICS_STALE_TIME = 10 * 60 * 1000;

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

  const { data: patterns, isLoading: patternsLoading } = useQuery({
    queryKey: ["analytics", "patterns"],
    queryFn: () => analyticsApi.patterns().then((response) => response.data),
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
      hint: "Reply rate on tracked applications.",
      icon: <TrendUp size={18} weight="bold" />,
      tone: "success" as const,
    },
    {
      key: "latency",
      label: "Avg days to response",
      value: loadingOverview ? "..." : summary.avg_days_to_response.toFixed(1),
      hint: "Mean time from application to reply.",
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
          description="Track discovery volume, application outcomes, response quality, and source health."
          meta={
            <>
              <Badge variant="info" size="sm">
                Live charts
              </Badge>
              <Badge variant="success" size="sm">
                Source feed
              </Badge>
              <Badge variant="secondary" size="sm">
                30 day window
              </Badge>
            </>
          }
        />

        <MetricStrip items={metrics} />
      </motion.div>

      <SplitWorkspace
        primary={
          <AnalyticsPrimaryColumn
            daily={daily}
            funnel={funnel}
            sources={sources}
            skills={skills}
            patterns={patterns}
            patternsLoading={patternsLoading}
          />
        }
        secondary={
          <AnalyticsSecondaryRail
            loadingOverview={loadingOverview}
            summary={{
              total_interviews: summary.total_interviews,
              total_offers: summary.total_offers,
            }}
            sources={sources}
          />
        }
      />
    </div>
  );
}
