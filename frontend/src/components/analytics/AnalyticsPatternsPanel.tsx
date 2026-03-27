import { Funnel, TrendUp, WarningCircle } from "@phosphor-icons/react";
import type { AnalyticsPatternsResponse } from "../../api/analytics";
import { SectionHeader } from "../system/SectionHeader";
import { Surface } from "../system/Surface";
import Badge from "../ui/Badge";
import EmptyState from "../ui/EmptyState";
import Skeleton from "../ui/Skeleton";

function PatternStat({
  label,
  value,
  hint,
}: {
  label: string;
  value: string;
  hint: string;
}) {
  return (
    <div className="border-2 border-border bg-[var(--color-bg-tertiary)] p-3">
      <div className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-text-muted">
        {label}
      </div>
      <div className="mt-3 text-xl font-black tracking-[-0.05em] text-text-primary">{value}</div>
      <p className="mt-2 text-sm leading-6 text-text-secondary">{hint}</p>
    </div>
  );
}

export function AnalyticsPatternsPanel({
  patterns,
  loading = false,
}: {
  patterns: AnalyticsPatternsResponse | null | undefined;
  loading?: boolean;
}) {
  const bestSize = [...(patterns?.callback_rate_by_company_size ?? [])].sort(
    (left, right) => right.callback_rate - left.callback_rate
  )[0];
  const responsePattern = patterns?.response_time_patterns?.[0] ?? null;
  const bestTiming = [...(patterns?.best_application_timing ?? [])].sort(
    (left, right) => right.callback_rate - left.callback_rate
  )[0];
  const worstGhosting = [...(patterns?.company_ghosting_rate ?? [])].sort(
    (left, right) => right.ghosting_rate - left.ghosting_rate
  )[0];
  const topSkillGaps = patterns?.skill_gap_detection?.slice(0, 6) ?? [];
  const funnel = (patterns?.conversion_funnel ?? []).filter((entry) => entry.count > 0);

  const hasAnyPattern =
    !!bestSize ||
    !!responsePattern ||
    !!bestTiming ||
    !!worstGhosting ||
    topSkillGaps.length > 0 ||
    funnel.length > 0;

  return (
    <Surface tone="default" padding="lg" radius="xl">
      <SectionHeader
        title="Application patterns"
        description="Callback, timing, ghosting, funnel, and skill gaps from live application history."
      />

      {loading ? (
        <div className="mt-5 space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            {Array.from({ length: 4 }).map((_, index) => (
              <div key={index} className="border-2 border-border bg-[var(--color-bg-tertiary)] p-3">
                <Skeleton variant="text" className="h-4 w-32" />
                <Skeleton variant="text" className="mt-4 h-7 w-24" />
                <Skeleton variant="text" className="mt-3 h-4 w-3/4" />
              </div>
            ))}
          </div>
          <Surface tone="subtle" padding="md">
            <Skeleton variant="text" className="h-4 w-40" />
            <div className="mt-4 flex flex-wrap gap-2">
              {Array.from({ length: 3 }).map((_, index) => (
                <Skeleton key={index} variant="text" className="h-8 w-24" />
              ))}
            </div>
          </Surface>
        </div>
      ) : !hasAnyPattern ? (
        <div className="mt-4">
          <EmptyState
            icon={<TrendUp size={34} weight="bold" />}
            title="No pattern data yet"
            description="Pattern analysis will appear after enough application history exists."
          />
        </div>
      ) : (
        <div className="mt-5 space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <PatternStat
              label="Best company size"
              value={bestSize ? `${bestSize.size_bucket} - ${bestSize.callback_rate.toFixed(1)}%` : "No sample"}
              hint={
                bestSize
                  ? `${bestSize.callbacks}/${bestSize.total_applications} callbacks`
                  : "Not enough applications to compare company size buckets."
              }
            />
            <PatternStat
              label="Response time"
              value={
                responsePattern?.warning
                  ? responsePattern.warning
                  : responsePattern
                    ? `${responsePattern.avg_days_to_response.toFixed(1)} days`
                    : "No sample"
              }
              hint={
                responsePattern
                  ? `${responsePattern.sample_size} application responses in sample`
                  : "Response timing is not available yet."
              }
            />
            <PatternStat
              label="Best day"
              value={bestTiming ? `${bestTiming.day_of_week} - ${bestTiming.callback_rate.toFixed(1)}%` : "No sample"}
              hint={
                bestTiming
                  ? `${bestTiming.callbacks}/${bestTiming.total_applications} callbacks`
                  : "Not enough dated applications to compare weekdays."
              }
            />
            <PatternStat
              label="Ghosting watch"
              value={worstGhosting ? `${worstGhosting.company} - ${worstGhosting.ghosting_rate.toFixed(1)}%` : "No sample"}
              hint={
                worstGhosting
                  ? `${worstGhosting.ghosted}/${worstGhosting.total_applications} ghosted applications`
                  : "No company ghosting pattern yet."
              }
            />
          </div>

          <Surface tone="subtle" padding="md">
            <div className="flex items-center gap-2 font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-text-muted">
              <Funnel size={14} weight="bold" className="text-accent-primary" />
              Conversion funnel
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              {funnel.length ? (
                funnel.map((entry) => (
                  <Badge key={entry.stage} variant="secondary">
                    {entry.stage}: {entry.count}
                  </Badge>
                ))
              ) : (
                <span className="text-sm text-text-secondary">No funnel transitions recorded.</span>
              )}
            </div>
          </Surface>

          <Surface tone="subtle" padding="md">
            <div className="flex items-center gap-2 font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-text-muted">
              <WarningCircle size={14} weight="bold" className="text-accent-warning" />
              Skill gaps
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              {topSkillGaps.length ? (
                topSkillGaps.map((entry) => (
                  <Badge key={entry.skill} variant="warning">
                    {entry.skill} ({entry.demand_count})
                  </Badge>
                ))
              ) : (
                <span className="text-sm text-text-secondary">No repeated skill gaps detected.</span>
              )}
            </div>
          </Surface>
        </div>
      )}
    </Surface>
  );
}
