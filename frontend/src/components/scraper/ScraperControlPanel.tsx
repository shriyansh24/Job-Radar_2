import { ArrowClockwise, Play } from "@phosphor-icons/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { scraperApi, type ScraperRun } from "../../api/scraper";

const statusColors: Record<string, string> = {
  completed: "bg-[var(--color-accent-secondary-subtle)] text-[var(--color-accent-secondary)]",
  running: "bg-[var(--color-accent-info-subtle)] text-[var(--color-accent-info)]",
  failed: "bg-[var(--color-accent-danger-subtle)] text-[var(--color-accent-danger)]",
};

export default function ScraperControlPanel() {
  const queryClient = useQueryClient();
  const { data, isLoading, refetch } = useQuery({
    queryKey: ["scraper", "runs"],
    queryFn: () => scraperApi.runs().then((r) => r.data),
    refetchInterval: 15_000,
  });

  const [triggeringSource, setTriggeringSource] = useState<string | null>(null);

  const triggerMutation = useMutation({
    mutationFn: (source: string) => {
      setTriggeringSource(source);
      return scraperApi.triggerScraper();
    },
    onSuccess: () => {
      setTriggeringSource(null);
      queryClient.invalidateQueries({ queryKey: ["scraper", "runs"] });
    },
    onError: () => {
      setTriggeringSource(null);
    },
  });

  const runs = data ?? [];
  const isRunning = runs.some((r) => r.status === "running");

  // Group runs by source, take latest per source
  const latestBySource = new Map<string, ScraperRun>();
  for (const run of runs) {
    if (!latestBySource.has(run.source) || run.started_at > latestBySource.get(run.source)!.started_at) {
      latestBySource.set(run.source, run);
    }
  }

  return (
    <div className="border border-border rounded-[var(--radius-lg)] bg-bg-secondary">
      <div className="flex items-center justify-between px-4 py-3 border-b border-border">
        <h3 className="text-sm font-medium text-text-primary">Scraper Status</h3>
        <button
          onClick={() => refetch()}
          className="p-1.5 rounded-[var(--radius-md)] hover:bg-bg-tertiary text-text-secondary transition-colors"
          title="Refresh"
        >
          <ArrowClockwise size={16} weight="bold" className={isLoading ? "animate-spin" : ""} />
        </button>
      </div>

      {isRunning && (
        <div className="border-b border-border bg-[var(--color-accent-info-subtle)] px-4 py-2 text-xs text-[var(--color-accent-info)]">
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-[var(--color-accent-info)] animate-pulse" />
          Scraper is running...
          </div>
        </div>
      )}

      <div className="divide-y divide-border">
        {Array.from(latestBySource.entries()).map(([source, run]) => {
          const isTriggeringThis = triggeringSource === source && triggerMutation.isPending;
          return (
            <div key={source} className="flex items-center justify-between px-4 py-2.5 text-sm">
              <div className="flex items-center gap-3 min-w-0">
                <span className="font-medium text-text-primary capitalize w-24 truncate">
                  {source}
                </span>
                <span
                  className={`px-2 py-0.5 rounded text-xs font-medium ${
                    statusColors[run.status] ?? "bg-bg-tertiary text-text-muted"
                  }`}
                >
                  {run.status}
                </span>
              </div>
              <div className="flex items-center gap-4 text-xs text-text-muted shrink-0">
                <span>{run.jobs_found} found</span>
                <span>{run.jobs_new} new</span>
                {run.duration_seconds != null && <span>{run.duration_seconds}s</span>}
                <span>{new Date(run.started_at).toLocaleTimeString()}</span>
                <button
                  onClick={() => triggerMutation.mutate(source)}
                  disabled={isTriggeringThis || run.status === "running"}
                  className="flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-medium bg-bg-tertiary text-text-secondary hover:bg-accent-primary/10 hover:text-accent-primary disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  title="Run Now"
                >
                  <Play size={10} weight="bold" className={isTriggeringThis ? "animate-pulse" : ""} />
                  {isTriggeringThis ? "Running..." : "Run Now"}
                </button>
              </div>
            </div>
          );
        })}

        {latestBySource.size === 0 && !isLoading && (
          <div className="px-4 py-6 text-center text-sm text-text-muted">
            No scraper runs yet
          </div>
        )}
      </div>
    </div>
  );
}
