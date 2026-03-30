import { format } from "date-fns";
import type { AutoApplyRun } from "../../api/auto-apply";
import Badge from "../ui/Badge";
import { statusVariant } from "./autoApplyUtils";

export function RunRow({ run }: { run: AutoApplyRun }) {
  return (
    <div className="border-t-2 border-[var(--color-text-primary)] px-4 py-4 first:border-t-0 sm:px-5">
      <div className="grid gap-3 md:grid-cols-[minmax(0,1.2fr)_repeat(4,minmax(100px,1fr))]">
        <div className="min-w-0">
          <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-text-muted">Job</div>
          <div className="mt-1 truncate text-sm font-semibold text-text-primary">{run.job_id.slice(0, 8)}...</div>
        </div>
        <div>
          <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-text-muted">Status</div>
          <div className="mt-1">
            <Badge variant={statusVariant(run.status)} size="sm">
              {run.status}
            </Badge>
          </div>
        </div>
        <div>
          <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-text-muted">ATS</div>
          <div className="mt-1 text-sm text-text-secondary">{run.ats_provider || "-"}</div>
        </div>
        <div>
          <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-text-muted">
            Fields Filled
          </div>
          <div className="mt-1 text-sm text-text-secondary">
            {Object.keys(run.fields_filled).length} filled
            {run.fields_missed.length ? (
              <span className="ml-1 text-accent-danger">({run.fields_missed.length} missed)</span>
            ) : null}
          </div>
        </div>
        <div>
          <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-text-muted">Time</div>
          <div className="mt-1 text-sm text-text-secondary">
            {run.completed_at
              ? format(new Date(run.completed_at), "PP p")
              : run.started_at
                ? format(new Date(run.started_at), "PP p")
                : "-"}
          </div>
        </div>
      </div>
    </div>
  );
}
