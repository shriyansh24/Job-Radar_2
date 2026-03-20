import { GitMerge, WarningCircle } from "@phosphor-icons/react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { canonicalJobsApi, type CanonicalJob } from "../api/phase7a";

export default function CanonicalJobs() {
  const [showStale, setShowStale] = useState(false);
  const qc = useQueryClient();

  const { data: jobs = [], isLoading } = useQuery({
    queryKey: ["canonical-jobs", { stale_only: showStale }],
    queryFn: () => canonicalJobsApi.list({ stale_only: showStale }),
  });

  const closeMut = useMutation({
    mutationFn: canonicalJobsApi.close,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["canonical-jobs"] }),
  });

  const reactivateMut = useMutation({
    mutationFn: canonicalJobsApi.reactivate,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["canonical-jobs"] }),
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-text-primary flex items-center gap-2">
          <GitMerge size={24} weight="bold" />
          Canonical Jobs
        </h1>
        <button
          onClick={() => setShowStale(!showStale)}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-[var(--radius-md)] text-sm transition-colors ${
            showStale
              ? "bg-yellow-500/10 text-yellow-400"
              : "bg-bg-tertiary text-text-secondary hover:text-text-primary"
          }`}
        >
          <WarningCircle size={16} />
          {showStale ? "Showing stale" : "Show stale only"}
        </button>
      </div>

      {isLoading ? (
        <div className="text-text-muted text-sm">Loading...</div>
      ) : jobs.length === 0 ? (
        <div className="text-center py-12 text-text-muted">
          <GitMerge size={48} className="mx-auto mb-3 opacity-50" />
          <p>No canonical jobs found</p>
        </div>
      ) : (
        <div className="space-y-3">
          {jobs.map((job: CanonicalJob) => (
            <div
              key={job.id}
              className="border border-border rounded-[var(--radius-lg)] p-4 bg-bg-secondary hover:bg-bg-tertiary/50 transition-colors"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0">
                  <h3 className="text-sm font-medium text-text-primary truncate">
                    {job.title}
                  </h3>
                  <p className="text-xs text-text-secondary mt-0.5">
                    {job.company_name}
                    {job.location && ` \u2022 ${job.location}`}
                    {job.remote_type && ` \u2022 ${job.remote_type}`}
                  </p>
                  <div className="flex items-center gap-3 mt-2 text-xs text-text-muted">
                    <span>{job.source_count} source(s)</span>
                    <span>
                      First seen {new Date(job.first_seen_at).toLocaleDateString()}
                    </span>
                    {job.is_stale && (
                      <span className="text-yellow-400 flex items-center gap-1">
                        <WarningCircle size={12} /> Stale
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex gap-2 shrink-0">
                  {job.status === "open" ? (
                    <button
                      onClick={() => closeMut.mutate(job.id)}
                      className="px-3 py-1 rounded-[var(--radius-md)] text-xs bg-red-500/10 text-red-400 hover:bg-red-500/20 transition-colors"
                    >
                      Close
                    </button>
                  ) : (
                    <button
                      onClick={() => reactivateMut.mutate(job.id)}
                      className="px-3 py-1 rounded-[var(--radius-md)] text-xs bg-green-500/10 text-green-400 hover:bg-green-500/20 transition-colors"
                    >
                      Reactivate
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
