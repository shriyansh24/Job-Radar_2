import { MetricStrip } from "../system/MetricStrip";
import { BRUTAL_PANEL } from "./constants";

type ProfileMetricsProps = {
  searchQueryCount: number;
  watchlistCount: number;
  educationCount: number;
  experienceCount: number;
};

function ProfileMetrics({ searchQueryCount, watchlistCount, educationCount, experienceCount }: ProfileMetricsProps) {
  return (
    <MetricStrip
      items={[
        { key: "queries", label: "Search seeds", value: searchQueryCount, hint: "Titles or phrases that shape discovery." },
        { key: "watchlist", label: "Watchlist", value: watchlistCount, hint: "Companies you want tracked." },
        { key: "education", label: "Education entries", value: educationCount, hint: "Academic context used in prep." },
        { key: "experience", label: "Experience entries", value: experienceCount, hint: "Role history surfaced to Copilot and interview prep." },
      ]}
      className={`${BRUTAL_PANEL} [&>div]:!rounded-none [&>div]:!border-2 [&>div]:!border-[var(--color-text-primary)] [&>div]:!bg-[var(--color-bg-secondary)] [&>div]:!shadow-[4px_4px_0px_0px_var(--color-text-primary)]`}
    />
  );
}

export { ProfileMetrics };
export type { ProfileMetricsProps };
