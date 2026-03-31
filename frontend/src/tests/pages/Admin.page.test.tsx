import { render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, expect, it, vi } from "vitest";
import Admin from "../../pages/Admin";

vi.mock("../../api/admin", () => ({
  adminApi: {
    health: () =>
      Promise.resolve({ data: { status: "ok", database: "connected" } }),
    diagnostics: () =>
      Promise.resolve({
        data: {
          python_version: "3.13",
          platform: "Windows",
          job_count: 0,
          application_count: 0,
        },
      }),
    runtime: () =>
      Promise.resolve({
        data: {
          status: "ok",
          captured_at: "2026-03-31T12:00:00+00:00",
          redis_connected: true,
          queue_summary: {
            overall_pressure: "nominal",
            overall_alert: "clear",
            queues: [],
          },
          worker_metrics: [],
          auth_audit_sink: {
            enabled: true,
            stream_key: "jobradar:auth-audit",
            maxlen: 1000,
          },
          queue_alert_routing: {
            stream_key: "jobradar:queue-alerts",
            stream_maxlen: 1000,
            webhook_enabled: false,
            webhook_host: null,
          },
          recent_queue_samples: [
            {
              stream_id: "1-0",
              captured_at: "2026-03-31T11:45:00+00:00",
              overall_pressure: "elevated",
              overall_alert: "watch",
              queues: [
                {
                  queue_name: "arq:queue:scraping",
                  queue_depth: 3,
                  queue_pressure: "elevated",
                  oldest_job_age_seconds: 45,
                  queue_alert: "watch",
                },
              ],
            },
          ],
          recent_queue_alerts: [
            {
              stream_id: "2-0",
              captured_at: "2026-03-31T11:46:00+00:00",
              scope: "queue",
              queue_name: "arq:queue:scraping",
              previous_pressure: "nominal",
              current_pressure: "elevated",
              previous_alert: "clear",
              current_alert: "watch",
              queue_depth: 3,
              oldest_job_age_seconds: 45,
            },
          ],
          recent_auth_audit_events: [
            {
              stream_id: "3-0",
              event: "auth_login_succeeded",
              audit_stream: "auth",
              timestamp: "2026-03-31T11:47:00+00:00",
              request_id: "req-1",
              user_id: "user-1",
              auth_source: "password",
            },
          ],
        },
      }),
    sourceHealth: () => Promise.resolve({ data: [] }),
    reindex: () => Promise.resolve({ data: {} }),
    exportData: () => Promise.resolve({ data: new Blob(["{}"]) }),
    importData: () => Promise.resolve({ data: {} }),
  },
}));

function renderAdmin() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <Admin />
    </QueryClientProvider>
  );
}

describe("Admin", () => {
  it("does not expose the misleading rebuild embeddings action", async () => {
    renderAdmin();

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /reindex fts/i })).toBeInTheDocument();
    });

    expect(screen.queryByRole("button", { name: /rebuild embeddings/i })).not.toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /runtime signals/i })).toBeInTheDocument();
    expect(await screen.findByText("Queue routing")).toBeInTheDocument();
    expect(await screen.findByText("Queue samples")).toBeInTheDocument();
    expect(await screen.findByText("Queue alerts")).toBeInTheDocument();
    expect(await screen.findByText("Auth audit")).toBeInTheDocument();
  });
});
