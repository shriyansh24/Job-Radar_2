import { Briefcase } from "@phosphor-icons/react";
import type { Job } from "../../api/jobs";
import JobDetail from "./JobDetail";
import { StateBlock } from "../system/StateBlock";
import { Surface } from "../system/Surface";

export function JobDetailPanel({
  selectedJobId,
  isLoadingDetail,
  selectedJob,
  onClose,
}: {
  selectedJobId: string | null;
  isLoadingDetail: boolean;
  selectedJob: Job | null;
  onClose: () => void;
}) {
  return (
    <Surface tone="default" padding="none" className="overflow-hidden xl:sticky xl:top-6">
      {selectedJobId ? (
        isLoadingDetail ? (
          <div className="space-y-4 p-5 sm:p-6">
            <div className="h-10 animate-pulse border-2 border-border bg-[var(--color-bg-tertiary)]" />
            <div className="h-4 animate-pulse border-2 border-border bg-[var(--color-bg-tertiary)]" />
            <div className="h-40 animate-pulse border-2 border-border bg-[var(--color-bg-tertiary)]" />
          </div>
        ) : selectedJob ? (
          <JobDetail job={selectedJob} onClose={onClose} />
        ) : (
          <div className="p-5 sm:p-6">
            <StateBlock tone="muted" title="Select a job" description="Open a result to inspect details." icon={<Briefcase size={16} weight="bold" />} />
          </div>
        )
      ) : (
        <div className="p-5 sm:p-6">
          <StateBlock tone="muted" title="Select a job" description="Open a result to inspect details." icon={<Briefcase size={16} weight="bold" />} />
        </div>
      )}
    </Surface>
  );
}
