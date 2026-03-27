import type { ScrapeAttempt } from "../../api/scraper";
import { attemptStatusIcon, relativeTime } from "./targetUtils";
import { cn } from "../../lib/utils";

export function AttemptTimeline({ attempts }: { attempts: ScrapeAttempt[] }) {
  if (!attempts.length) {
    return <p className="text-xs italic text-text-muted">No attempts recorded yet.</p>;
  }

  return (
    <div className="space-y-2">
      {attempts.slice(0, 5).map((attempt) => (
        <div key={attempt.id} className="brutal-panel flex items-start gap-3 px-4 py-3">
          <div className="mt-0.5">{attemptStatusIcon(attempt.status)}</div>
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-mono text-[11px] font-bold uppercase tracking-[0.16em] text-text-primary">
                Tier {attempt.actual_tier_used}
              </span>
              <span
                className={cn(
                  "font-mono text-[11px] font-bold uppercase tracking-[0.16em]",
                  attempt.status === "success" ? "text-accent-success" : "text-accent-danger"
                )}
              >
                {attempt.status}
              </span>
              <span className="text-xs text-text-muted">
                {attempt.jobs_extracted} job{attempt.jobs_extracted !== 1 ? "s" : ""}
              </span>
              {attempt.duration_ms != null ? (
                <span className="text-xs text-text-muted">
                  {(attempt.duration_ms / 1000).toFixed(1)}s
                </span>
              ) : null}
            </div>
            {attempt.error_message ? (
              <p className="mt-0.5 truncate text-xs text-accent-danger" title={attempt.error_message}>
                {attempt.error_message}
              </p>
            ) : null}
            <p className="mt-0.5 text-xs text-text-muted">{relativeTime(attempt.created_at)}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
