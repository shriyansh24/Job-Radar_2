import type { AnalyticsOverview } from "../../api/analytics";

export const DEFAULT_OVERVIEW: AnalyticsOverview = {
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

export const PIPELINE_STAGES = [
  { key: "saved", label: "Saved" },
  { key: "applied", label: "Applied" },
  { key: "screening", label: "Screening" },
  { key: "interviewing", label: "Interviewing" },
  { key: "offer", label: "Offer" },
  { key: "accepted", label: "Accepted" },
] as const;

export const DASHBOARD_METRIC_SPECS = [
  { key: "jobs", label: "Total jobs", hint: "Jobs in feed.", tone: "default" as const },
  { key: "applications", label: "Applications", hint: "Tracked applications.", tone: "default" as const },
  { key: "interviews", label: "Interviews", hint: "Active interviews.", tone: "warning" as const },
  { key: "offers", label: "Offers", hint: "Open offers.", tone: "success" as const },
] as const;
