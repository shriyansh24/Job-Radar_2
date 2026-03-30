import { CheckCircle, Clock, XCircle } from "@phosphor-icons/react";

import type { AutoApplyRun } from "../../api/auto-apply";
import { SectionHeader } from "../system/SectionHeader";
import { SplitWorkspace } from "../system/SplitWorkspace";
import { StateBlock } from "../system/StateBlock";
import { Surface } from "../system/Surface";
import EmptyState from "../ui/EmptyState";
import { SkeletonCard } from "../ui/Skeleton";
import { RunRow } from "./RunRow";

type AutoApplyHistoryTabPanelProps = {
  runs: AutoApplyRun[] | undefined;
  runsLoading: boolean;
  successfulCount: number;
  failedCount: number;
};

export function AutoApplyHistoryTabPanel({
  runs,
  runsLoading,
  successfulCount,
  failedCount,
}: AutoApplyHistoryTabPanelProps) {
  return (
    <SplitWorkspace
      primary={
        <Surface padding="none" radius="xl" className="overflow-hidden">
          <div className="border-b-2 border-[var(--color-text-primary)] bg-bg-tertiary px-5 py-4">
            <SectionHeader title="Run History" description="Recent attempts and field coverage." />
          </div>
          {runsLoading ? (
            <div className="space-y-3 p-5">
              {Array.from({ length: 3 }).map((_, index) => (
                <SkeletonCard key={index} />
              ))}
            </div>
          ) : !runs?.length ? (
            <div className="p-5">
              <EmptyState
                icon={<Clock size={40} weight="bold" />}
                title="No run history"
                description="Runs will appear here after auto-apply starts."
              />
            </div>
          ) : (
            <div>
              {runs.map((run) => (
                <RunRow key={run.id} run={run} />
              ))}
            </div>
          )}
        </Surface>
      }
      secondary={
        <div className="space-y-4">
          <StateBlock
            tone="success"
            icon={<CheckCircle size={18} weight="bold" />}
            title="Success signal"
            description={`${successfulCount} completed runs are tracked.`}
          />
          <StateBlock
            tone="danger"
            icon={<XCircle size={18} weight="bold" />}
            title="Failure watch"
            description={
              failedCount
                ? `${failedCount} runs failed. Inspect field coverage.`
                : "No failed runs are currently recorded."
            }
          />
        </div>
      }
    />
  );
}
