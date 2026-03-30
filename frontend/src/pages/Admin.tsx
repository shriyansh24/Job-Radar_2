import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState, type ChangeEvent } from "react";
import { adminApi, type SourceHealth } from "../api/admin";
import { PageHeader, SplitWorkspace } from "../components/system";
import { toast } from "../components/ui/toastService";
import { AdminDiagnosticsPanel } from "../components/admin/AdminDiagnosticsPanel";
import { AdminHealthSummaryPanel } from "../components/admin/AdminHealthSummaryPanel";
import { AdminMaintenanceActionsPanel } from "../components/admin/AdminMaintenanceActionsPanel";
import { AdminSourceHealthTable } from "../components/admin/AdminSourceHealthTable";

export default function Admin() {
  const queryClient = useQueryClient();
  const [sortKey, setSortKey] = useState<string | undefined>();
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("asc");
  const [clearDataOpen, setClearDataOpen] = useState(false);

  const { data: health, isLoading: loadingHealth } = useQuery({
    queryKey: ["admin", "health"],
    queryFn: () => adminApi.health().then((response) => response.data),
    refetchInterval: 30_000,
  });

  const { data: diagnostics, isLoading: loadingDiagnostics } = useQuery({
    queryKey: ["admin", "diagnostics"],
    queryFn: () => adminApi.diagnostics().then((response) => response.data),
  });

  const { data: sources, isLoading: loadingSources } = useQuery({
    queryKey: ["admin", "sourceHealth"],
    queryFn: () => adminApi.sourceHealth().then((response) => response.data),
  });

  const reindexMutation = useMutation({
    mutationFn: () => adminApi.reindex(),
    onSuccess: () => toast("success", "Full-text search reindex started"),
    onError: () => toast("error", "Failed to start reindex"),
  });

  const exportMutation = useMutation({
    mutationFn: () => adminApi.exportData(),
    onSuccess: (response) => {
      const blob = new Blob([response.data as BlobPart]);
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `jobradar-export-${new Date().toISOString().slice(0, 10)}.json`;
      anchor.click();
      URL.revokeObjectURL(url);
      toast("success", "Data exported successfully");
    },
    onError: () => toast("error", "Failed to export data"),
  });

  const importMutation = useMutation({
    mutationFn: async (file: File) => {
      const text = await file.text();
      const data = JSON.parse(text);
      return adminApi.importData(data);
    },
    onSuccess: () => {
      toast("success", "Data imported successfully");
      queryClient.invalidateQueries({ queryKey: ["admin"] });
    },
    onError: () => toast("error", "Failed to import data"),
  });

  const clearDataMutation = useMutation({
    mutationFn: () => adminApi.clearData(),
    onSuccess: async (response) => {
      setClearDataOpen(false);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["admin"] }),
        queryClient.invalidateQueries({ queryKey: ["jobs"] }),
        queryClient.invalidateQueries({ queryKey: ["pipeline"] }),
      ]);
      toast("success", `Cleared ${response.data.rows_deleted} rows`);
    },
    onError: () => toast("error", "Failed to clear data"),
  });

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (file) {
      importMutation.mutate(file);
      event.target.value = "";
    }
  }

  function handleSort(key: string) {
    if (sortKey === key) {
      setSortOrder((previous) => (previous === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortOrder("asc");
    }
  }

  const sortedSources = useMemo(() => {
    const items = [...(sources ?? [])];

    return items.sort((left, right) => {
      if (!sortKey) return 0;

      const leftValue = left[sortKey as keyof SourceHealth];
      const rightValue = right[sortKey as keyof SourceHealth];

      if (leftValue == null || rightValue == null) return 0;

      const comparison = leftValue < rightValue ? -1 : leftValue > rightValue ? 1 : 0;
      return sortOrder === "asc" ? comparison : -comparison;
    });
  }, [sortKey, sortOrder, sources]);

  const dbOnline =
    health?.database === "connected" ||
    health?.database === "ok" ||
    health?.database === "healthy";
  const healthySources =
    sources?.filter((source) => source.health_state === "healthy").length ?? 0;
  const totalJobs = diagnostics?.job_count ?? diagnostics?.total_jobs ?? "-";
  const applicationCount = diagnostics?.application_count ?? "-";
  const runtimePlatform = diagnostics?.platform ?? "-";

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Operations"
        title="Admin"
        description="System health, diagnostics, source telemetry, and maintenance actions."
        meta={
          <>
            <span className="border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-tertiary)] px-3 py-2 font-mono text-[10px] font-bold uppercase tracking-[0.16em]">
              API {health?.status ?? "unknown"}
            </span>
            <span className="border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-tertiary)] px-3 py-2 font-mono text-[10px] font-bold uppercase tracking-[0.16em]">
              DB {dbOnline ? "online" : "offline"}
            </span>
            <span className="border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-tertiary)] px-3 py-2 font-mono text-[10px] font-bold uppercase tracking-[0.16em]">
              {healthySources}/{sources?.length ?? 0} healthy
            </span>
          </>
        }
      />

      <SplitWorkspace
        primary={
          <AdminHealthSummaryPanel
            loading={loadingHealth}
            apiStatus={health?.status ?? "unknown"}
            dbOnline={dbOnline}
            healthySources={healthySources}
            sourceCount={sources?.length ?? 0}
          />
        }
        secondary={
          <AdminDiagnosticsPanel
            loading={loadingDiagnostics}
            pythonVersion={diagnostics?.python_version ?? "-"}
            platform={runtimePlatform}
            applicationCount={applicationCount}
            totalJobs={totalJobs}
          />
        }
      />

      <AdminSourceHealthTable
        loading={loadingSources}
        sortedSources={sortedSources}
        sourceCount={sources?.length ?? 0}
        sortKey={sortKey}
        sortOrder={sortOrder}
        onSort={handleSort}
      />

      <AdminMaintenanceActionsPanel
        onReindex={() => reindexMutation.mutate()}
        reindexPending={reindexMutation.isPending}
        onExport={() => exportMutation.mutate()}
        exportPending={exportMutation.isPending}
        onImportFile={handleFileChange}
        importPending={importMutation.isPending}
        clearDataOpen={clearDataOpen}
        onRequestClearData={() => setClearDataOpen(true)}
        onCancelClearData={() => setClearDataOpen(false)}
        onConfirmClearData={() => clearDataMutation.mutate()}
        clearDataPending={clearDataMutation.isPending}
      />
    </div>
  );
}
