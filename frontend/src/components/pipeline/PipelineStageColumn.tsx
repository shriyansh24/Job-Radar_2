import type { Application } from "../../api/pipeline";
import Badge from "../ui/Badge";
import { SkeletonCard } from "../ui/Skeleton";
import { StateBlock } from "../system/StateBlock";
import { Surface } from "../system/Surface";
import { cn } from "../../lib/utils";
import { PipelineStageCard } from "./PipelineStageCard";
import { NEXT_STAGE } from "./pipelineWorkflow";

const STAGE_TONES: Record<string, string> = {
  saved: "bg-[var(--color-text-muted)]",
  applied: "bg-[var(--color-accent-primary)]",
  screening: "bg-[var(--color-accent-primary-subtle)]",
  interviewing: "bg-[var(--color-accent-warning)]",
  offer: "bg-[var(--color-accent-success)]",
  accepted: "bg-[var(--color-accent-success)]",
};

export function PipelineStageColumn({
  label,
  keyName,
  applications,
  selectedId,
  onSelect,
  onAdvance,
  advancingId,
  loading,
}: {
  label: string;
  keyName: string;
  applications: Application[];
  selectedId: string | null;
  onSelect: (application: Application) => void;
  onAdvance: (application: Application) => void;
  advancingId: string | null;
  loading: boolean;
}) {
  const tone = STAGE_TONES[keyName] ?? "bg-[var(--color-accent-primary)]";

  return (
    <Surface tone="default" padding="none" className="xl:min-w-[18rem] xl:flex-[0_0_18rem]">
      <div className={cn("h-2 border-b-2 border-border", tone)} />
      <div className="p-4">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <span className={cn("h-2.5 w-2.5 border border-border", tone)} />
            <span className="text-sm font-semibold uppercase tracking-[-0.04em] text-foreground">
              {label}
            </span>
          </div>
          <Badge variant="secondary">{applications.length}</Badge>
        </div>

        <div className="mt-4 space-y-3">
          {loading ? (
            Array.from({ length: 2 }).map((_, index) => <SkeletonCard key={index} />)
          ) : applications.length === 0 ? (
            <StateBlock tone="muted" title="No applications" description="No records are in this stage." />
          ) : (
            applications.map((application) => (
              <PipelineStageCard
                key={application.id}
                application={application}
                selected={selectedId === application.id}
                onSelect={() => onSelect(application)}
                onAdvance={() => onAdvance(application)}
                isAdvancing={advancingId === application.id}
                canAdvance={!!NEXT_STAGE[application.status]}
              />
            ))
          )}
        </div>
      </div>
    </Surface>
  );
}
