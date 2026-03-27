import { ArrowRight, Buildings } from "@phosphor-icons/react";
import type { Application } from "../../api/pipeline";
import Button from "../ui/Button";
import { StateBlock } from "../system/StateBlock";
import { Surface } from "../system/Surface";
import { NEXT_STAGE } from "./pipelineWorkflow";

export function PipelineDetailPanel({
  selectedApplication,
  firstApplicationId,
  advancingId,
  onAdvance,
  onSelectFirst,
}: {
  selectedApplication: Application | null;
  firstApplicationId: string | null;
  advancingId: string | null;
  onAdvance: (application: Application) => void;
  onSelectFirst: () => void;
}) {
  return (
    <Surface tone="default" padding="none" className="overflow-hidden xl:sticky xl:top-6">
      <div className="border-b-2 border-border bg-[var(--color-bg-tertiary)] px-5 py-4 sm:px-6">
        <div className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-text-muted">
          Selected
        </div>
        <h2 className="mt-1 font-display text-xl font-black uppercase tracking-[-0.05em] text-foreground">
          Details
        </h2>
      </div>

      {selectedApplication ? (
        <div className="space-y-4 p-5 sm:p-6">
          <StateBlock
            tone="muted"
            title={selectedApplication.status}
            description={`${selectedApplication.position_title ?? "Untitled application"}${selectedApplication.company_name ? ` - ${selectedApplication.company_name}` : ""}`}
            icon={<Buildings size={18} weight="bold" />}
          />

          <div className="grid gap-3 sm:grid-cols-2">
            <StateBlock tone="muted" title="Source" description={selectedApplication.source ?? "Unknown"} />
            <StateBlock
              tone="muted"
              title="Salary"
              description={
                selectedApplication.salary_offered
                  ? `$${selectedApplication.salary_offered.toLocaleString()}`
                  : "Not recorded"
              }
            />
          </div>

          <StateBlock tone="muted" title="Notes" description={selectedApplication.notes || "No notes yet."} />

          <div className="flex flex-wrap gap-2">
            {NEXT_STAGE[selectedApplication.status] ? (
              <Button
                variant="primary"
                loading={advancingId === selectedApplication.id}
                onClick={() => onAdvance(selectedApplication)}
                icon={<ArrowRight size={16} weight="bold" />}
              >
                Advance
              </Button>
            ) : null}
            {firstApplicationId ? <Button variant="secondary" onClick={onSelectFirst}>First record</Button> : null}
          </div>
        </div>
      ) : (
        <div className="p-5 sm:p-6">
          <StateBlock tone="muted" title="Select an application" description="Choose a record to inspect details." />
        </div>
      )}
    </Surface>
  );
}
