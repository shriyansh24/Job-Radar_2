import { Star } from "@phosphor-icons/react";
import type { Job } from "../../api/jobs";
import { cn } from "../../lib/utils";
import Badge from "../ui/Badge";
import { Surface } from "../system/Surface";
import { freshnessLabel, freshnessVariant, scoreLabel } from "./jobBoardUtils";

export function JobResultRow({
  job,
  selected,
  onClick,
}: {
  job: Job;
  selected: boolean;
  onClick: () => void;
}) {
  const match = scoreLabel(job.match_score);
  const freshness = freshnessLabel(job.freshness_score);

  return (
    <Surface
      tone="subtle"
      padding="md"
      interactive
      role="button"
      tabIndex={0}
      onClick={onClick}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          onClick();
        }
      }}
      className={cn(
        "group transition-transform duration-150 hover:-translate-y-1 hover:-translate-x-1",
        selected && "border-[var(--color-accent-primary)] bg-[var(--color-accent-primary-subtle)]"
      )}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-text-muted">
            {job.source ?? "source"}
          </div>
          <h3 className="mt-2 truncate font-display text-xl font-black uppercase tracking-[-0.05em] text-foreground">
            {job.title}
          </h3>
          <p className="mt-1 truncate text-sm text-muted-foreground">
            {job.company_name ?? "Unknown company"}
          </p>
        </div>

        <div className="flex shrink-0 flex-col items-end gap-2">
          {match ? <Badge variant="outline">{match}</Badge> : null}
          {freshness ? <Badge variant={freshnessVariant(job.freshness_score)}>{freshness}</Badge> : null}
          {job.is_starred ? (
            <Star size={16} weight="fill" className="text-[var(--color-accent-warning)]" />
          ) : null}
        </div>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        {job.location ? <Badge variant="secondary">{job.location}</Badge> : null}
        {job.remote_type ? <Badge variant="secondary">{job.remote_type}</Badge> : null}
        {job.job_type ? <Badge variant="secondary">{job.job_type}</Badge> : null}
        {job.experience_level ? <Badge variant="secondary">{job.experience_level}</Badge> : null}
      </div>
    </Surface>
  );
}
