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
  });
});
