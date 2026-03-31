import Badge from "../ui/Badge";
import EmptyState from "../ui/EmptyState";
import Skeleton from "../ui/Skeleton";
import { SectionHeader } from "../system/SectionHeader";
import { Surface } from "../system/Surface";
import type { RuntimeStatus } from "../../api/admin";

export function AdminRuntimePanel({
  loading,
  runtime,
}: {
  loading: boolean;
  runtime?: RuntimeStatus | null;
}) {
  const queueSummary = runtime?.queue_summary;
  const queueRows = queueSummary?.queues ?? [];
  const workerRows = runtime?.worker_metrics ?? [];

  return (
    <Surface className="border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-secondary)]">
      <SectionHeader
        title="Runtime signals"
        description="Queue pressure, worker heartbeats, and the dedicated auth audit sink."
      />

      {loading ? (
        <div className="mt-6 grid gap-3 lg:grid-cols-2">
          {Array.from({ length: 4 }).map((_, index) => (
            <div
              key={index}
              className="border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-secondary)] px-4 py-4"
            >
              <Skeleton variant="text" className="h-4 w-28" />
              <Skeleton variant="text" className="mt-4 h-5 w-40" />
            </div>
          ))}
        </div>
      ) : (
        <div className="mt-6 space-y-6">
          <div className="grid gap-3 sm:grid-cols-3">
            <div className="border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-secondary)] px-4 py-4">
              <p className="font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-text-muted">
                Redis
              </p>
              <div className="mt-4">
                <Badge variant={runtime?.redis_connected ? "success" : "danger"}>
                  {runtime?.redis_connected ? "Connected" : "Disconnected"}
                </Badge>
              </div>
            </div>
            <div className="border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-secondary)] px-4 py-4">
              <p className="font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-text-muted">
                Queue pressure
              </p>
              <div className="mt-4">
                <Badge variant={queueSummary?.overall_pressure === "stalled" ? "danger" : "warning"}>
                  {queueSummary?.overall_pressure ?? "unknown"}
                </Badge>
              </div>
            </div>
            <div className="border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-secondary)] px-4 py-4">
              <p className="font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-text-muted">
                Queue alert
              </p>
              <div className="mt-4">
                <Badge variant={queueSummary?.overall_alert === "critical" ? "danger" : "default"}>
                  {queueSummary?.overall_alert ?? "unknown"}
                </Badge>
              </div>
            </div>
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <div className="border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-secondary)]">
              <div className="border-b-2 border-border px-4 py-4">
                <p className="text-sm font-bold uppercase tracking-[0.18em]">Queue lanes</p>
              </div>
              {queueRows.length === 0 ? (
                <div className="p-4">
                  <EmptyState
                    title="No queue telemetry"
                    description="Queue snapshots will appear here once the scheduler and workers are connected."
                  />
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[42rem]">
                    <thead className="bg-[var(--color-bg-tertiary)]">
                      <tr className="border-b-2 border-border">
                        <th className="px-4 py-3 text-left text-[11px] font-bold uppercase tracking-[0.18em] text-text-muted">
                          Queue
                        </th>
                        <th className="px-4 py-3 text-left text-[11px] font-bold uppercase tracking-[0.18em] text-text-muted">
                          Depth
                        </th>
                        <th className="px-4 py-3 text-left text-[11px] font-bold uppercase tracking-[0.18em] text-text-muted">
                          Pressure
                        </th>
                        <th className="px-4 py-3 text-left text-[11px] font-bold uppercase tracking-[0.18em] text-text-muted">
                          Oldest job
                        </th>
                        <th className="px-4 py-3 text-left text-[11px] font-bold uppercase tracking-[0.18em] text-text-muted">
                          Alert
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {queueRows.map((queue) => (
                        <tr key={queue.queue_name} className="border-b-2 border-border last:border-b-0">
                          <td className="px-4 py-3 text-sm font-bold text-text-primary">{queue.queue_name}</td>
                          <td className="px-4 py-3 text-sm text-text-primary">{queue.queue_depth}</td>
                          <td className="px-4 py-3 text-sm text-text-primary">{queue.queue_pressure}</td>
                          <td className="px-4 py-3 text-sm text-text-primary">
                            {queue.oldest_job_age_seconds}s
                          </td>
                          <td className="px-4 py-3 text-sm text-text-primary">{queue.queue_alert}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            <div className="border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-secondary)]">
              <div className="border-b-2 border-border px-4 py-4">
                <p className="text-sm font-bold uppercase tracking-[0.18em]">Worker lanes</p>
              </div>
              {workerRows.length === 0 ? (
                <div className="p-4">
                  <EmptyState
                    title="No worker telemetry"
                    description="Worker metrics will appear once the queue lanes have reported a heartbeat."
                  />
                </div>
              ) : (
                <div className="space-y-0">
                  {workerRows.map((worker) => (
                    <div key={worker.role} className="border-b-2 border-border px-4 py-4 last:border-b-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <p className="text-sm font-bold uppercase tracking-[0.18em]">{worker.role}</p>
                        <Badge variant={worker.available ? "success" : "danger"}>
                          {worker.available ? "Heartbeat" : "Missing"}
                        </Badge>
                        {worker.queue_alert ? <Badge variant="default">{worker.queue_alert}</Badge> : null}
                      </div>
                      <p className="mt-2 text-sm text-text-secondary">
                        Queue {worker.queue_name ?? "unknown"} · depth {worker.queue_depth ?? 0} · pressure{" "}
                        {worker.queue_pressure ?? "unknown"} · oldest{" "}
                        {worker.oldest_job_age_seconds ?? 0}s
                      </p>
                      <p className="mt-1 text-xs text-text-muted">
                        completed {worker.queue_job_completed_total ?? 0} · failed{" "}
                        {worker.queue_job_failed_total ?? 0} · retried {worker.retry_scheduled_total ?? 0} · exhausted{" "}
                        {worker.retry_exhausted_total ?? 0}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div className="border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-secondary)] px-4 py-4">
            <p className="text-sm font-bold uppercase tracking-[0.18em]">Auth audit sink</p>
            <p className="mt-2 text-sm text-text-secondary">
              {runtime?.auth_audit_sink.enabled
                ? `Redis stream ${runtime?.auth_audit_sink.stream_key} is enabled with maxlen ${runtime?.auth_audit_sink.maxlen}.`
                : "Auth audit streaming is disabled."}
            </p>
            <p className="mt-1 text-xs text-text-muted">Captured at {runtime?.captured_at ?? "unknown"}.</p>
          </div>
        </div>
      )}
    </Surface>
  );
}
