import { StateBlock } from "../system/StateBlock";
import { Surface } from "../system/Surface";
import type { Application } from "../../api/pipeline";
import { PipelineStageColumn } from "./PipelineStageColumn";
import { PIPELINE_STAGES } from "./pipelineWorkflow";

export function PipelineBoard({
  isLoading,
  isError,
  stageColumns,
  selectedApplicationId,
  onSelect,
  onAdvance,
  advancingId,
}: {
  isLoading: boolean;
  isError: boolean;
  stageColumns: { key: string; label: string; applications: Application[] }[];
  selectedApplicationId: string | null;
  onSelect: (application: Application) => void;
  onAdvance: (application: Application) => void;
  advancingId: string | null;
}) {
  return (
    <Surface tone="default" padding="none" className="overflow-hidden">
      <div className="border-b-2 border-border bg-[var(--color-bg-tertiary)] px-5 py-4 sm:px-6">
        <div>
          <div className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-text-muted">
            Pipeline
          </div>
          <h2 className="mt-1 font-display text-xl font-black uppercase tracking-[-0.05em] text-foreground sm:text-2xl">
            Stages
          </h2>
        </div>
      </div>

      <div className="p-4">
        {isLoading ? (
          <div className="grid gap-4 md:grid-cols-2 xl:flex xl:overflow-x-auto">
            {Array.from({ length: PIPELINE_STAGES.length }).map((_, index) => (
              <div
                key={index}
                className="h-64 border-2 border-border bg-[var(--color-bg-tertiary)] xl:min-w-[18rem] xl:flex-[0_0_18rem]"
              />
            ))}
          </div>
        ) : isError ? (
          <StateBlock tone="danger" title="Failed to load the pipeline" description="Try again in a moment." />
        ) : (
          <div className="grid gap-4 md:grid-cols-2 xl:flex xl:overflow-x-auto">
            {stageColumns.map((stage) => (
              <PipelineStageColumn
                key={stage.key}
                keyName={stage.key}
                label={stage.label}
                applications={stage.applications}
                selectedId={selectedApplicationId}
                onSelect={onSelect}
                onAdvance={onAdvance}
                advancingId={advancingId}
                loading={false}
              />
            ))}
          </div>
        )}
      </div>
    </Surface>
  );
}
