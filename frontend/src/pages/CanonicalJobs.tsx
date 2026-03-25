import { GitMerge, WarningCircle } from "@phosphor-icons/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { canonicalJobsApi, type CanonicalJob } from "../api/phase7a";
import { PageHeader, SectionHeader, Surface } from "../components/system";
import Badge from "../components/ui/Badge";
import Button from "../components/ui/Button";
import EmptyState from "../components/ui/EmptyState";
import Skeleton from "../components/ui/Skeleton";
import { cn } from "../lib/utils";

export default function CanonicalJobs() {
  const [showStale, setShowStale] = useState(false);
  const queryClient = useQueryClient();

  const { data: jobs = [], isLoading } = useQuery({
    queryKey: ["canonical-jobs", { stale_only: showStale }],
    queryFn: () => canonicalJobsApi.list({ stale_only: showStale }),
  });

  const closeMutation = useMutation({
    mutationFn: canonicalJobsApi.close,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["canonical-jobs"] }),
  });

  const reactivateMutation = useMutation({
    mutationFn: canonicalJobsApi.reactivate,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["canonical-jobs"] }),
  });

  const staleCount = useMemo(() => jobs.filter((job) => job.is_stale).length, [jobs]);
  const openCount = useMemo(() => jobs.filter((job) => job.status === "open").length, [jobs]);

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Operations"
        title="Canonical Jobs"
        description="Merged job entities, source consolidation, and stale record cleanup for the canonical registry."
        actions={
          <button
            type="button"
            onClick={() => setShowStale(!showStale)}
            className={cn(
              "hard-press inline-flex items-center gap-2 border-2 border-border px-3 py-2 font-mono text-[10px] font-bold uppercase tracking-[0.18em] transition-[background-color,color,border-color] duration-[var(--transition-fast)]",
              showStale
                ? "bg-[var(--color-accent-warning-subtle)] text-[var(--color-accent-warning)] shadow-[var(--shadow-sm)]"
                : "bg-card text-text-secondary hover:text-text-primary"
            )}
          >
            <WarningCircle size={14} weight="bold" />
            {showStale ? "Showing stale" : "Show stale only"}
          </button>
        }
        meta={
          <>
            <span className="border-2 border-border bg-[var(--color-bg-tertiary)] px-3 py-2 font-mono font-bold uppercase tracking-[0.16em]">
              {jobs.length} loaded
            </span>
            <span className="border-2 border-border bg-[var(--color-bg-tertiary)] px-3 py-2 font-mono font-bold uppercase tracking-[0.16em]">
              {openCount} open
            </span>
            <span className="border-2 border-border bg-[var(--color-bg-tertiary)] px-3 py-2 font-mono font-bold uppercase tracking-[0.16em]">
              {staleCount} stale
            </span>
          </>
        }
      />

      {isLoading ? (
        <div className="space-y-4">
          {Array.from({ length: 4 }).map((_, index) => (
            <Surface key={index}>
              <Skeleton variant="text" className="h-5 w-40" />
              <Skeleton variant="text" className="mt-4 h-4 w-56" />
              <div className="mt-5 grid gap-3 sm:grid-cols-3">
                <Skeleton variant="text" className="h-4 w-20" />
                <Skeleton variant="text" className="h-4 w-20" />
                <Skeleton variant="text" className="h-4 w-20" />
              </div>
            </Surface>
          ))}
        </div>
      ) : jobs.length === 0 ? (
        <EmptyState
          icon={<GitMerge size={40} weight="bold" />}
          title="No canonical jobs found"
          description="The canonical queue will appear here once source jobs are merged."
        />
      ) : (
        <Surface padding="none">
          <div className="border-b-2 border-border px-5 py-5">
            <SectionHeader
              title="Canonical Queue"
              description="Monitor merged job records, source coverage, and stale lifecycle actions."
              action={
                <div className="font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-text-muted">
                  {jobs.length} rows
                </div>
              }
            />
          </div>

          <div className="divide-y-2 divide-border">
            {jobs.map((job: CanonicalJob) => (
              <div key={job.id} className="px-5 py-5">
                <div className="grid gap-5 xl:grid-cols-[minmax(0,1.6fr)_220px_180px] xl:items-start">
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <h3 className="text-xl font-black uppercase tracking-[-0.05em] text-text-primary">
                        {job.title}
                      </h3>
                      <Badge variant={job.status === "open" ? "info" : "default"}>{job.status}</Badge>
                      {job.is_stale ? <Badge variant="warning">Stale</Badge> : null}
                    </div>

                    <p className="mt-3 text-sm text-text-secondary">
                      {job.company_name}
                      {job.location ? ` | ${job.location}` : ""}
                      {job.remote_type ? ` | ${job.remote_type}` : ""}
                    </p>

                    <div className="mt-4 flex flex-wrap gap-2">
                      <span className="border-2 border-border bg-[var(--color-bg-tertiary)] px-3 py-2 font-mono text-[10px] font-bold uppercase tracking-[0.16em] text-text-secondary">
                        {job.source_count} source(s)
                      </span>
                      <span className="border-2 border-border bg-[var(--color-bg-tertiary)] px-3 py-2 font-mono text-[10px] font-bold uppercase tracking-[0.16em] text-text-secondary">
                        First seen {new Date(job.first_seen_at).toLocaleDateString()}
                      </span>
                      <span className="border-2 border-border bg-[var(--color-bg-tertiary)] px-3 py-2 font-mono text-[10px] font-bold uppercase tracking-[0.16em] text-text-secondary">
                        Refreshed {new Date(job.last_refreshed_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>

                  <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
                    <div className="border-2 border-border bg-[var(--color-bg-tertiary)] px-4 py-3">
                      <p className="font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-text-muted">
                        Company
                      </p>
                      <p className="mt-3 text-sm text-text-primary">{job.company_name}</p>
                    </div>
                    <div className="border-2 border-border bg-[var(--color-bg-tertiary)] px-4 py-3">
                      <p className="font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-text-muted">
                        Domain
                      </p>
                      <p className="mt-3 text-sm text-text-primary">{job.company_domain ?? "-"}</p>
                    </div>
                  </div>

                  <div className="flex flex-wrap items-center gap-3 xl:justify-end">
                    {job.status === "open" ? (
                      <Button
                        variant="danger"
                        size="sm"
                        loading={closeMutation.isPending}
                        onClick={() => closeMutation.mutate(job.id)}
                      >
                        Close
                      </Button>
                    ) : (
                      <Button
                        variant="success"
                        size="sm"
                        loading={reactivateMutation.isPending}
                        onClick={() => reactivateMutation.mutate(job.id)}
                      >
                        Reactivate
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Surface>
      )}
    </div>
  );
}
