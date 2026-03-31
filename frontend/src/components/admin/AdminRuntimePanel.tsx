import Badge from "../ui/Badge";
import EmptyState from "../ui/EmptyState";
import Skeleton from "../ui/Skeleton";
import { SectionHeader } from "../system/SectionHeader";
import { Surface } from "../system/Surface";
import type { RuntimeStatus } from "../../api/admin";

function summarizeHistoryItems(items: number, label: string) {
  return `${items} ${label}`;
}

function queuePressureVariant(pressure?: string) {
  if (pressure === "saturated") return "danger";
  if (pressure === "elevated") return "warning";
  return "default";
}

function queueAlertVariant(alert?: string) {
  if (alert === "stalled" || alert === "backlog") return "danger";
  if (alert === "watch") return "warning";
  return "default";
}

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
  const recentQueueSamples = runtime?.recent_queue_samples ?? [];
  const recentQueueAlerts = runtime?.recent_queue_alerts ?? [];
  const recentAuthEvents = runtime?.recent_auth_audit_events ?? [];
  const queueAlertRouting = runtime?.queue_alert_routing;

  return (
    <Surface className="border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-secondary)]">
      <SectionHeader
        title="Runtime signals"
        description="Queue pressure, worker heartbeats, recent queue events, and auth audit state."
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
                <Badge variant={queuePressureVariant(queueSummary?.overall_pressure)}>
                  {queueSummary?.overall_pressure ?? "unknown"}
                </Badge>
              </div>
            </div>
            <div className="border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-secondary)] px-4 py-4">
              <p className="font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-text-muted">
                Queue alert
              </p>
              <div className="mt-4">
                <Badge variant={queueAlertVariant(queueSummary?.overall_alert)}>
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
                        {worker.queue_alert ? (
                          <Badge variant={queueAlertVariant(worker.queue_alert)}>{worker.queue_alert}</Badge>
                        ) : null}
                      </div>
                      <p className="mt-2 text-sm text-text-secondary">
                        Queue {worker.queue_name ?? "unknown"} | depth {worker.queue_depth ?? 0} | pressure{" "}
                        {worker.queue_pressure ?? "unknown"} | oldest {worker.oldest_job_age_seconds ?? 0}s
                      </p>
                      <p className="mt-1 text-xs text-text-muted">
                        completed {worker.queue_job_completed_total ?? 0} | failed{" "}
                        {worker.queue_job_failed_total ?? 0} | retried {worker.retry_scheduled_total ?? 0} | exhausted{" "}
                        {worker.retry_exhausted_total ?? 0}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div className="grid gap-6 xl:grid-cols-3">
            <div className="border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-secondary)] px-4 py-4">
              <p className="text-sm font-bold uppercase tracking-[0.18em]">Queue routing</p>
              <p className="mt-2 text-sm text-text-secondary">
                {queueAlertRouting?.webhook_enabled
                  ? `Alerts route to ${queueAlertRouting.stream_key} and ${queueAlertRouting.webhook_host ?? "a webhook"}`
                  : `Alerts stay in ${queueAlertRouting?.stream_key ?? "the queue alert stream"}.`}
              </p>
              <p className="mt-1 text-xs text-text-muted">
                Stream maxlen {queueAlertRouting?.stream_maxlen ?? 0}
              </p>
            </div>

            <div className="border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-secondary)] px-4 py-4">
              <p className="text-sm font-bold uppercase tracking-[0.18em]">Queue samples</p>
              <p className="mt-2 text-sm text-text-secondary">
                {summarizeHistoryItems(recentQueueSamples.length, "samples")}
              </p>
              <div className="mt-3 space-y-3">
                {recentQueueSamples.length === 0 ? (
                  <p className="text-xs text-text-muted">No queue samples recorded yet.</p>
                ) : (
                  recentQueueSamples.slice(0, 3).map((sample) => (
                    <div key={sample.stream_id} className="border border-border px-3 py-2">
                      <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-text-muted">
                        {sample.captured_at}
                      </p>
                      <p className="mt-1 text-sm text-text-secondary">
                        {sample.overall_pressure} | {sample.overall_alert}
                      </p>
                      <p className="mt-1 text-xs text-text-muted">
                        {sample.queues.map((queue) => queue.queue_name).join(" | ") || "No queues"}
                      </p>
                    </div>
                  ))
                )}
              </div>
            </div>

            <div className="border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-secondary)] px-4 py-4">
              <p className="text-sm font-bold uppercase tracking-[0.18em]">Auth audit</p>
              <p className="mt-2 text-sm text-text-secondary">
                {summarizeHistoryItems(recentAuthEvents.length, "events")}
              </p>
              <div className="mt-3 space-y-3">
                {recentAuthEvents.length === 0 ? (
                  <p className="text-xs text-text-muted">No auth audit events captured yet.</p>
                ) : (
                  recentAuthEvents.slice(0, 3).map((event) => (
                    <div key={event.stream_id} className="border border-border px-3 py-2">
                      <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-text-muted">
                        {event.timestamp}
                      </p>
                      <p className="mt-1 text-sm text-text-secondary">{event.event}</p>
                      <p className="mt-1 text-xs text-text-muted">
                        {event.user_id ?? "anon"}
                        {event.reason ? ` | ${event.reason}` : ""}
                        {event.request_id ? ` | ${event.request_id}` : ""}
                      </p>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>

          <div className="border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-secondary)] px-4 py-4">
            <p className="text-sm font-bold uppercase tracking-[0.18em]">Queue alerts</p>
            <p className="mt-2 text-sm text-text-secondary">
              {summarizeHistoryItems(recentQueueAlerts.length, "events")}
            </p>
            <div className="mt-3 space-y-3">
              {recentQueueAlerts.length === 0 ? (
                <p className="text-xs text-text-muted">No queue alert transitions yet.</p>
              ) : (
                recentQueueAlerts.slice(0, 3).map((alert) => (
                  <div key={alert.stream_id} className="border border-border px-3 py-2">
                    <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-text-muted">
                      {alert.captured_at}
                    </p>
                    <p className="mt-1 text-sm text-text-secondary">
                      {alert.scope}
                      {alert.queue_name ? ` | ${alert.queue_name}` : ""}
                    </p>
                      <p className="mt-1 text-xs text-text-muted">
                      {alert.previous_pressure} to {alert.current_pressure} | {alert.previous_alert} to{" "}
                      {alert.current_alert}
                    </p>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </Surface>
  );
}
