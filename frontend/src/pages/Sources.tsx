import { Heartbeat, Pulse, ShieldCheck, WarningCircle } from "@phosphor-icons/react";
import { useQuery } from "@tanstack/react-query";
import { sourceHealthApi, type SourceHealth } from "../api/phase7a";
import { PageHeader, Surface } from "../components/system";
import Badge from "../components/ui/Badge";
import EmptyState from "../components/ui/EmptyState";
import Skeleton from "../components/ui/Skeleton";

function healthVariant(state: string): "success" | "warning" | "danger" | "default" {
  switch (state) {
    case "healthy":
      return "success";
    case "degraded":
      return "warning";
    case "unhealthy":
      return "danger";
    default:
      return "default";
  }
}

export default function Sources() {
  const { data: sources = [], isLoading } = useQuery({
    queryKey: ["source-health"],
    queryFn: sourceHealthApi.list,
    refetchInterval: 60_000,
  });

  const healthyCount = sources.filter((source) => source.health_state === "healthy").length;
  const totalJobs = sources.reduce((sum, source) => sum + source.total_jobs_found, 0);

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Operations"
        title="Source Health"
        description="Scraper source status, quality, and failure telemetry across the ingestion layer."
        meta={
          <>
            <span className="border-2 border-border bg-[var(--color-bg-tertiary)] px-3 py-2 font-mono font-bold uppercase tracking-[0.16em]">
              {sources.length} sources
            </span>
            <span className="border-2 border-border bg-[var(--color-bg-tertiary)] px-3 py-2 font-mono font-bold uppercase tracking-[0.16em]">
              {healthyCount} healthy
            </span>
          </>
        }
      />

      <div className="grid gap-4 md:grid-cols-3">
        <Surface tone="subtle" padding="md">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-text-muted">
                Sources
              </p>
              <p className="mt-3 text-3xl font-black uppercase tracking-[-0.05em] text-text-primary">
                {isLoading ? "..." : sources.length.toLocaleString()}
              </p>
            </div>
            <Heartbeat size={24} weight="bold" className="text-text-muted" />
          </div>
        </Surface>
        <Surface tone="subtle" padding="md">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-text-muted">
                Healthy
              </p>
              <p className="mt-3 text-3xl font-black uppercase tracking-[-0.05em] text-text-primary">
                {isLoading ? "..." : healthyCount.toLocaleString()}
              </p>
            </div>
            <ShieldCheck size={24} weight="fill" className="text-accent-secondary" />
          </div>
        </Surface>
        <Surface tone="subtle" padding="md">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-text-muted">
                Jobs Found
              </p>
              <p className="mt-3 text-3xl font-black uppercase tracking-[-0.05em] text-text-primary">
                {isLoading ? "..." : `${totalJobs.toLocaleString()} total`}
              </p>
            </div>
            <Pulse size={24} weight="bold" className="text-accent-primary" />
          </div>
        </Surface>
      </div>

      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {Array.from({ length: 6 }).map((_, index) => (
            <Surface key={index}>
              <Skeleton variant="text" className="h-4 w-28" />
              <Skeleton variant="text" className="mt-6 h-8 w-16" />
              <div className="mt-6 space-y-3">
                <Skeleton variant="text" className="h-4 w-full" />
                <Skeleton variant="text" className="h-4 w-full" />
                <Skeleton variant="text" className="h-4 w-full" />
              </div>
            </Surface>
          ))}
        </div>
      ) : sources.length === 0 ? (
        <EmptyState
          icon={<WarningCircle size={40} weight="bold" />}
          title="No sources found"
          description="Source health will appear here once the scraper registry starts reporting."
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {sources.map((source: SourceHealth) => (
            <Surface key={source.id} className="h-full">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="text-lg font-black uppercase tracking-[-0.05em] text-text-primary">
                    {source.source_name}
                  </p>
                  <p className="mt-2 font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-text-muted">
                    monitored source
                  </p>
                </div>
                <Badge variant={healthVariant(source.health_state)}>{source.health_state}</Badge>
              </div>

              <div className="mt-6 grid gap-3 sm:grid-cols-2">
                <div className="border-2 border-border bg-[var(--color-bg-tertiary)] px-4 py-3">
                  <p className="font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-text-muted">
                    Quality
                  </p>
                  <p className="mt-3 text-2xl font-black uppercase tracking-[-0.05em] text-text-primary">
                    {(source.quality_score * 100).toFixed(0)}%
                  </p>
                </div>
                <div className="border-2 border-border bg-[var(--color-bg-tertiary)] px-4 py-3">
                  <p className="font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-text-muted">
                    Jobs found
                  </p>
                  <p className="mt-3 text-2xl font-black uppercase tracking-[-0.05em] text-text-primary">
                    {source.total_jobs_found}
                  </p>
                </div>
              </div>

              <div className="mt-6 space-y-3 border-t-2 border-border pt-4">
                <div className="flex items-center justify-between gap-4 text-sm">
                  <span className="text-text-muted">Failures</span>
                  <span className="font-mono text-text-primary">{source.failure_count}</span>
                </div>
                <div className="flex items-center justify-between gap-4 text-sm">
                  <span className="text-text-muted">Last check</span>
                  <span className="text-right text-text-secondary">
                    {source.last_check_at
                      ? new Date(source.last_check_at).toLocaleString()
                      : "Never"}
                  </span>
                </div>
                <div className="flex items-center justify-between gap-4 text-sm">
                  <span className="text-text-muted">Created</span>
                  <span className="text-right text-text-secondary">
                    {new Date(source.created_at).toLocaleDateString()}
                  </span>
                </div>
              </div>
            </Surface>
          ))}
        </div>
      )}
    </div>
  );
}
