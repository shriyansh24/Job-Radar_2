import { ArrowClockwise, Clock, Lightning, Pause, Play } from "@phosphor-icons/react";
import type { AutoApplyRun } from "../../api/auto-apply";
import { SectionHeader } from "../system/SectionHeader";
import { StateBlock } from "../system/StateBlock";
import { Surface } from "../system/Surface";
import Button from "../ui/Button";

type AutoApplyOperatorControlsPanelProps = {
  onRefresh: () => void;
  onPause: () => void;
  onRun: () => void;
  pausePending: boolean;
  runPending: boolean;
  operatorBusy: boolean;
};

export function AutoApplyOperatorControlsPanel({
  onRefresh,
  onPause,
  onRun,
  pausePending,
  runPending,
  operatorBusy,
}: AutoApplyOperatorControlsPanelProps) {
  return (
    <Surface padding="lg" radius="xl">
      <SectionHeader
        title="Operator controls"
        description="Trigger a run, pause submission, and refresh queue state."
      />
      <div className="mt-5 flex flex-wrap gap-3">
        <Button
          loading={runPending}
          disabled={operatorBusy}
          onClick={onRun}
          icon={<Play size={14} weight="bold" />}
        >
          Run now
        </Button>
        <Button
          variant="secondary"
          loading={pausePending}
          disabled={operatorBusy}
          onClick={onPause}
          icon={<Pause size={14} weight="bold" />}
        >
          Pause
        </Button>
        <Button
          variant="secondary"
          onClick={onRefresh}
          icon={<ArrowClockwise size={14} weight="bold" />}
        >
          Refresh status
        </Button>
      </div>
    </Surface>
  );
}

type AutoApplyLatestRunPanelProps = {
  latestRun: AutoApplyRun | null;
  pendingCount: number;
};

export function AutoApplyLatestRunPanel({
  latestRun,
  pendingCount,
}: AutoApplyLatestRunPanelProps) {
  return (
    <Surface padding="lg" radius="xl">
      <SectionHeader title="Latest run" description="Most recent execution attempt and queue posture." />
      <div className="mt-5 grid gap-4 sm:grid-cols-2">
        <StateBlock
          tone={
            latestRun?.status === "failed"
              ? "danger"
              : latestRun?.status === "running" || pendingCount
                ? "warning"
                : latestRun
                  ? "success"
                  : "muted"
          }
          icon={<Lightning size={18} weight="bold" />}
          title={latestRun ? latestRun.status : "Idle"}
          description={
            latestRun
              ? `${latestRun.ats_provider ?? "Unknown ATS"} - ${Object.keys(latestRun.fields_filled ?? {}).length} fields filled`
              : "No execution has been recorded yet."
          }
        />
        <StateBlock
          tone={pendingCount ? "warning" : "success"}
          icon={<Clock size={18} weight="bold" />}
          title="Queue"
          description={
            pendingCount
              ? `${pendingCount} run${pendingCount === 1 ? "" : "s"} pending`
              : "No runs waiting."
          }
        />
      </div>
      {latestRun ? (
        <div className="mt-4 rounded-none border-2 border-border bg-bg-tertiary p-4">
          <div className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-text-muted">
            Run details
          </div>
          <div className="mt-3 grid gap-3 text-sm text-text-secondary sm:grid-cols-2">
            <div>
              <span className="font-semibold text-text-primary">Job</span>
              <div className="mt-1 break-all">{latestRun.job_id}</div>
            </div>
            <div>
              <span className="font-semibold text-text-primary">Missed fields</span>
              <div className="mt-1">{latestRun.fields_missed.length || 0}</div>
            </div>
          </div>
          {latestRun.error_message ? (
            <p className="mt-3 text-sm leading-6 text-[var(--color-accent-danger)]">
              {latestRun.error_message}
            </p>
          ) : null}
        </div>
      ) : null}
    </Surface>
  );
}
