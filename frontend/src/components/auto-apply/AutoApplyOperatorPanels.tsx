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
    <Surface padding="lg" radius="xl" data-testid="auto-apply-operator-controls">
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
  reviewCount: number;
};

export function AutoApplyLatestRunPanel({
  latestRun,
  pendingCount,
  reviewCount,
}: AutoApplyLatestRunPanelProps) {
  return (
    <Surface padding="lg" radius="xl">
      <SectionHeader title="Latest run" description="Most recent execution attempt and review posture." />
      <div className="mt-5 grid gap-4 sm:grid-cols-3">
        <StateBlock
          tone={
            latestRun?.status === "failed"
              ? "danger"
              : latestRun?.review_required || latestRun?.status === "filled"
                ? "warning"
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
        <StateBlock
          tone={reviewCount ? "warning" : "success"}
          icon={<Lightning size={18} weight="bold" />}
          title="Review notes"
          description={
            reviewCount
              ? `${reviewCount} recorded run${reviewCount === 1 ? "" : "s"} include manual review notes.`
              : "No recorded runs include manual review notes."
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
              <div className="mt-1 break-all">{latestRun.job_id ?? "Unlinked job"}</div>
            </div>
            <div>
              <span className="font-semibold text-text-primary">Missed fields</span>
              <div className="mt-1">{latestRun.fields_missed.length || 0}</div>
            </div>
          </div>
          {latestRun.review_items.length ? (
            <div className="mt-3 space-y-2">
              <div className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-text-muted">
                Review items
              </div>
              <ul className="space-y-1 text-sm text-text-secondary">
                {latestRun.review_items.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          ) : null}
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
