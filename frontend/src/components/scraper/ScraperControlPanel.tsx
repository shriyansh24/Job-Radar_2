import {
  ArrowClockwise,
  Lightning,
  MagnifyingGlass,
  Pulse,
  Warning,
} from "@phosphor-icons/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { ComponentProps } from "react";

import { scraperApi, type ScraperRun, type ScraperRunResult, type TriggerBatchResult } from "../../api/scraper";
import { StateBlock } from "../system/StateBlock";
import { Surface } from "../system/Surface";
import Badge from "../ui/Badge";
import Button from "../ui/Button";
import { toast } from "../ui/toastService";

const STATUS_VARIANTS: Record<string, ComponentProps<typeof Badge>["variant"]> = {
  completed: "success",
  completed_with_errors: "warning",
  running: "info",
  failed: "danger",
};

function formatRunLabel(source: string) {
  if (source === "batch_trigger") {
    return "Target batch";
  }
  if (source === "manual_trigger") {
    return "Manual target run";
  }
  if (source.includes(",")) {
    return "Profile query sweep";
  }
  return source.replace(/_/g, " ");
}

function formatStatus(status: string) {
  return status.replace(/_/g, " ");
}

function formatTimestamp(value: string | null) {
  if (!value) return "Not recorded";
  return new Date(value).toLocaleString();
}

function summarizeSearchSweep(result: ScraperRunResult) {
  const results = result.results ?? [];
  const jobsFound = results.reduce((sum, item) => sum + (item.jobs_found ?? 0), 0);
  const errors = results.filter((item) => item.error).length;
  return { jobsFound, errors };
}

export default function ScraperControlPanel() {
  const queryClient = useQueryClient();

  const { data, isLoading, refetch } = useQuery({
    queryKey: ["scraper", "runs"],
    queryFn: () => scraperApi.runs().then((response) => response.data),
    refetchInterval: 15_000,
  });

  const triggerSearchMutation = useMutation({
    mutationFn: () => scraperApi.triggerScraper().then((response) => response.data),
    onSuccess: (result: ScraperRunResult) => {
      const summary = summarizeSearchSweep(result);
      toast(
        "success",
        summary.errors
          ? `Search sweep finished with ${summary.errors} source errors`
          : `Search sweep finished - ${summary.jobsFound} jobs found`
      );
      void queryClient.invalidateQueries({ queryKey: ["scraper", "runs"] });
    },
    onError: () => toast("error", "Search sweep failed"),
  });

  const triggerBatchMutation = useMutation({
    mutationFn: () => scraperApi.triggerBatch().then((response) => response.data),
    onSuccess: (result: TriggerBatchResult) => {
      toast(
        "success",
        `Batch completed - ${result.jobs_found} jobs found across ${result.targets_attempted} targets`
      );
      void queryClient.invalidateQueries({ queryKey: ["scraper", "runs"] });
      void queryClient.invalidateQueries({ queryKey: ["targets"] });
    },
    onError: () => toast("error", "Batch trigger failed"),
  });

  const runs = data ?? [];
  const runningCount = runs.filter((run) => run.status === "running").length;
  const failedCount = runs.filter(
    (run) => run.status === "failed" || run.status === "completed_with_errors" || !!run.error_message
  ).length;
  const latestCompletedRun = runs.find((run) => run.completed_at) ?? null;
  const recentRuns = runs.slice(0, 5);

  return (
    <Surface tone="default" padding="lg" radius="xl" className="hero-panel">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="space-y-1">
          <div className="command-label">Operator</div>
          <h2 className="font-headline text-2xl font-black uppercase tracking-tight">
            Scraper activity
          </h2>
          <p className="text-sm text-muted-foreground">
            Run the live search sweep or the target batch.
          </p>
        </div>

        <div className="flex flex-wrap gap-2">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => void refetch()}
            loading={isLoading}
            icon={<ArrowClockwise size={14} weight="bold" />}
          >
            Refresh
          </Button>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => triggerSearchMutation.mutate()}
            loading={triggerSearchMutation.isPending}
            icon={<MagnifyingGlass size={14} weight="bold" />}
          >
            Run search sweep
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={() => triggerBatchMutation.mutate()}
            loading={triggerBatchMutation.isPending}
            icon={<Lightning size={14} weight="bold" />}
          >
            Run target batch
          </Button>
        </div>
      </div>

      <div className="mt-5 grid gap-3 sm:grid-cols-3">
        <div className="brutal-panel px-4 py-3">
          <p className="font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-text-muted">
            Recent runs
          </p>
          <p className="mt-3 text-2xl font-black uppercase tracking-[-0.05em] text-text-primary">
            {runs.length}
          </p>
        </div>
        <div className="brutal-panel px-4 py-3">
          <p className="font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-text-muted">
            Running now
          </p>
          <p className="mt-3 text-2xl font-black uppercase tracking-[-0.05em] text-text-primary">
            {runningCount}
          </p>
        </div>
        <div className="brutal-panel px-4 py-3">
          <p className="font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-text-muted">
            Latest completion
          </p>
          <p className="mt-3 text-sm text-text-primary">
            {latestCompletedRun ? formatTimestamp(latestCompletedRun.completed_at) : "No completed runs"}
          </p>
        </div>
      </div>

      <div className="mt-5 space-y-3">
        {recentRuns.length === 0 && !isLoading ? (
          <StateBlock
            tone="muted"
            icon={<Pulse size={18} weight="bold" />}
            title="No runs recorded"
            description="Use the control actions above to start a profile-query sweep or a target batch."
          />
        ) : (
          recentRuns.map((run: ScraperRun) => (
            <div
              key={run.id}
              className="brutal-panel flex flex-col gap-3 px-4 py-3 lg:flex-row lg:items-center lg:justify-between"
            >
              <div className="space-y-1">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-sm font-black uppercase tracking-[-0.03em] text-text-primary">
                    {formatRunLabel(run.source)}
                  </span>
                  <Badge variant={STATUS_VARIANTS[run.status] ?? "default"}>
                    {formatStatus(run.status)}
                  </Badge>
                  {run.error_message ? (
                    <Badge variant="warning">attention</Badge>
                  ) : null}
                </div>
                <p className="text-xs text-text-muted">
                  Started {formatTimestamp(run.started_at)}
                  {run.completed_at ? ` • Finished ${formatTimestamp(run.completed_at)}` : ""}
                </p>
                {run.error_message ? (
                  <div className="mt-2 flex items-start gap-2 text-sm text-accent-warning">
                    <Warning size={14} weight="bold" className="mt-0.5 shrink-0" />
                    <span>{run.error_message}</span>
                  </div>
                ) : null}
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs text-text-secondary sm:grid-cols-4">
                <div>
                  <div className="font-mono font-bold uppercase tracking-[0.16em] text-text-muted">
                    Found
                  </div>
                  <div className="mt-1 text-sm text-text-primary">{run.jobs_found}</div>
                </div>
                <div>
                  <div className="font-mono font-bold uppercase tracking-[0.16em] text-text-muted">
                    New
                  </div>
                  <div className="mt-1 text-sm text-text-primary">{run.jobs_new}</div>
                </div>
                <div>
                  <div className="font-mono font-bold uppercase tracking-[0.16em] text-text-muted">
                    Updated
                  </div>
                  <div className="mt-1 text-sm text-text-primary">{run.jobs_updated}</div>
                </div>
                <div>
                  <div className="font-mono font-bold uppercase tracking-[0.16em] text-text-muted">
                    Duration
                  </div>
                  <div className="mt-1 text-sm text-text-primary">
                    {run.duration_seconds != null ? `${run.duration_seconds}s` : "-"}
                  </div>
                </div>
              </div>
            </div>
          ))
        )}

        {failedCount > 0 ? (
          <p className="text-xs text-accent-warning">
            {failedCount} recent run{failedCount === 1 ? "" : "s"} finished with errors.
          </p>
        ) : null}
      </div>
    </Surface>
  );
}
