import { CaretLeft, CaretRight } from "@phosphor-icons/react";
import type { Job } from "../../api/jobs";
import Button from "../ui/Button";
import { StateBlock } from "../system/StateBlock";
import { Surface } from "../system/Surface";
import { JobResultRow } from "./JobResultRow";

export function JobResultsPanel({
  searchMode,
  jobs,
  total,
  isLoading,
  isError,
  semanticReady,
  selectedJobId,
  onSelectJob,
  currentPage,
  totalPages,
  onPrevPage,
  onNextPage,
}: {
  searchMode: "exact" | "semantic";
  jobs: Job[];
  total: number;
  isLoading: boolean;
  isError: boolean;
  semanticReady: boolean;
  selectedJobId: string | null;
  onSelectJob: (jobId: string) => void;
  currentPage: number;
  totalPages: number;
  onPrevPage: () => void;
  onNextPage: () => void;
}) {
  return (
    <Surface tone="default" padding="none" className="overflow-hidden">
      <div className="flex items-center justify-between gap-3 border-b-2 border-border bg-[var(--color-bg-tertiary)] px-5 py-4 sm:px-6">
        <div>
          <div className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-text-muted">
            Results
          </div>
          <div className="mt-1 font-display text-xl font-black uppercase tracking-[-0.05em] text-foreground">
            {searchMode === "semantic" ? "Matches" : "Results"}
          </div>
        </div>
        <div className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-text-muted">
          {total.toLocaleString()} total
        </div>
      </div>

      <div className="max-h-[72vh] overflow-auto p-3 sm:p-4">
        {isError ? (
          <StateBlock tone="danger" title="Failed to load jobs" description="Try again in a moment." />
        ) : isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 8 }).map((_, index) => (
              <div
                key={index}
                className="h-24 animate-pulse border-2 border-border bg-[var(--color-bg-tertiary)]"
              />
            ))}
          </div>
        ) : searchMode === "semantic" && !semanticReady ? (
          <StateBlock
            tone="muted"
            title="Enter a semantic query"
            description="Use at least 2 characters to run semantic search."
          />
        ) : jobs.length === 0 ? (
          <StateBlock
            tone="muted"
            title={searchMode === "semantic" ? "No semantic matches" : "No jobs found"}
            description={searchMode === "semantic" ? "Try a broader search." : "Adjust the filters or search query."}
          />
        ) : (
          <div className="space-y-3">
            {jobs.map((job) => (
              <JobResultRow
                key={job.id}
                job={job}
                selected={job.id === selectedJobId}
                onClick={() => onSelectJob(job.id)}
              />
            ))}
          </div>
        )}
      </div>

      {searchMode === "exact" && totalPages > 1 ? (
        <div className="flex items-center justify-between border-t-2 border-border px-5 py-4 sm:px-6">
          <span className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-text-muted">
            Page <span className="text-foreground">{currentPage}</span> /{" "}
            <span className="text-foreground">{totalPages}</span>
          </span>
          <div className="flex gap-2">
            <Button variant="secondary" size="sm" disabled={currentPage <= 1} onClick={onPrevPage} icon={<CaretLeft size={14} weight="bold" />}>
              Prev
            </Button>
            <Button variant="secondary" size="sm" disabled={currentPage >= totalPages} onClick={onNextPage} icon={<CaretRight size={14} weight="bold" />}>
              Next
            </Button>
          </div>
        </div>
      ) : null}
    </Surface>
  );
}
