import { Clock, TrendUp } from "@phosphor-icons/react";
import type { ReactNode } from "react";
import { Surface } from "../system/Surface";
import { SectionHeader } from "../system/SectionHeader";
import EmptyState from "../ui/EmptyState";
import { cn } from "../../lib/utils";

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

type AnalyticsSourceRow = {
  source: string;
  total_jobs: number;
  quality_score: number;
  avg_match_score: number | null;
};

type AnalyticsSecondaryRailProps = {
  loadingOverview: boolean;
  summary: {
    total_interviews: number;
    total_offers: number;
  };
  sources: AnalyticsSourceRow[] | undefined;
};

function AnalyticsSecondaryRail({
  loadingOverview,
  summary,
  sources,
}: AnalyticsSecondaryRailProps) {
  return (
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
          icon={<Clock size={18} weight="bold" className="text-accent-warning" />}
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
                      {source.avg_match_score ? `${(source.avg_match_score * 100).toFixed(0)}%` : "-"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="mt-4">
            <EmptyState
              icon={<TrendUp size={34} weight="bold" />}
              title="No source quality yet"
              description="Once scrapers and saved searches have data, the quality table will appear here."
            />
          </div>
        )}
      </Surface>
    </div>
  );
}

export { AnalyticsSecondaryRail };
