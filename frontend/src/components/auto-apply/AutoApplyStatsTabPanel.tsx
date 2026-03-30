import {
  ChartBar,
  CheckCircle,
  Clock,
  Lightning,
  Pulse,
  ShieldCheck,
  XCircle,
} from "@phosphor-icons/react";

import type { AutoApplyStats } from "../../api/auto-apply";
import { SectionHeader } from "../system/SectionHeader";
import { StateBlock } from "../system/StateBlock";
import { Surface } from "../system/Surface";
import EmptyState from "../ui/EmptyState";
import { SkeletonCard } from "../ui/Skeleton";

type AutoApplyStatsTabPanelProps = {
  stats: AutoApplyStats | undefined;
  statsLoading: boolean;
  successRate: number;
};

export function AutoApplyStatsTabPanel({
  stats,
  statsLoading,
  successRate,
}: AutoApplyStatsTabPanelProps) {
  return (
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1.2fr)_minmax(320px,0.8fr)]">
      <Surface padding="lg" radius="xl">
        <SectionHeader
          title="Summary"
          description="Automation volume, queue state, and execution quality."
        />
        {statsLoading ? (
          <div className="mt-5 grid gap-4 sm:grid-cols-2">
            {Array.from({ length: 4 }).map((_, index) => (
              <SkeletonCard key={index} />
            ))}
          </div>
        ) : stats ? (
          <div className="mt-5 grid gap-4 sm:grid-cols-2">
            {[
              {
                label: "Total Runs",
                value: stats.total_runs,
                hint: "Attempts recorded end to end.",
                icon: <Pulse size={18} weight="bold" />,
              },
              {
                label: "Successful",
                value: stats.successful,
                hint: "Runs that completed cleanly.",
                icon: <CheckCircle size={18} weight="bold" />,
              },
              {
                label: "Failed",
                value: stats.failed,
                hint: "Runs requiring investigation.",
                icon: <XCircle size={18} weight="bold" />,
              },
              {
                label: "Pending",
                value: stats.pending,
                hint: "Items still in flight.",
                icon: <Clock size={18} weight="bold" />,
              },
            ].map((item) => (
              <Surface key={item.label} tone="subtle" padding="md">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-text-muted">
                      {item.label}
                    </div>
                    <div className="mt-3 text-4xl font-semibold tracking-[-0.06em] text-text-primary">
                      {item.value}
                    </div>
                    <p className="mt-2 text-sm leading-6 text-text-secondary">{item.hint}</p>
                  </div>
                  <div className="flex size-11 shrink-0 items-center justify-center border-2 border-[var(--color-text-primary)] bg-background">
                    {item.icon}
                  </div>
                </div>
              </Surface>
            ))}
          </div>
        ) : (
          <div className="mt-5">
            <EmptyState
              icon={<ChartBar size={40} weight="bold" />}
              title="No stats available"
              description="Stats will appear once auto-apply starts processing jobs."
            />
          </div>
        )}
      </Surface>

      <div className="space-y-4">
        <StateBlock
          tone="warning"
          icon={<Lightning size={18} weight="bold" />}
          title="Queue health"
          description={
            stats?.pending
              ? `There ${stats.pending === 1 ? "is" : "are"} ${stats.pending} pending application${stats.pending === 1 ? "" : "s"} in the queue.`
              : "No items are waiting in the queue."
          }
        />
        <StateBlock
          tone="success"
          icon={<ShieldCheck size={18} weight="bold" />}
          title="Conversion"
          description={`Current success rate is ${successRate}% based on recorded runs.`}
        />
      </div>
    </div>
  );
}
