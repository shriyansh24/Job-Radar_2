import {
  ArrowClockwise,
  Briefcase,
  Cloud,
  Clock,
  Database,
  DownloadSimple,
  UploadSimple,
  Warning,
} from "@phosphor-icons/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { formatDistanceToNow } from "date-fns";
import { useMemo, useRef, useState, type ChangeEvent, type ReactNode } from "react";
import { adminApi, type SourceHealth } from "../api/admin";
import { PageHeader, SectionHeader, SplitWorkspace, Surface } from "../components/system";
import Badge from "../components/ui/Badge";
import Button from "../components/ui/Button";
import EmptyState from "../components/ui/EmptyState";
import Skeleton from "../components/ui/Skeleton";
import { toast } from "../components/ui/toastService";
import { cn } from "../lib/utils";

function healthBadgeVariant(state: string): "success" | "warning" | "danger" | "default" {
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

function DiagnosticItem({
  icon,
  label,
  value,
  loading,
}: {
  icon: ReactNode;
  label: string;
  value: string | number;
  loading: boolean;
}) {
  return (
    <div className="brutal-panel px-4 py-4">
      <div className="flex items-start gap-3">
        <div className="mt-0.5 text-text-muted">{icon}</div>
        <div className="min-w-0 flex-1">
          <p className="font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-text-muted">
            {label}
          </p>
          {loading ? (
            <Skeleton variant="text" className="mt-3 h-5 w-24" />
          ) : (
            <p className="mt-3 text-lg font-black uppercase tracking-[-0.04em] text-text-primary">
              {value}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

const sourceHealthColumns: {
  key: string;
  label: string;
  sortable?: boolean;
  render?: (row: SourceHealth) => ReactNode;
}[] = [
  { key: "source_name", label: "Source", sortable: true },
  {
    key: "health_state",
    label: "Status",
    render: (row: SourceHealth) => (
      <Badge variant={healthBadgeVariant(row.health_state)}>{row.health_state}</Badge>
    ),
  },
  {
    key: "last_check_at",
    label: "Last Check",
    render: (row: SourceHealth) =>
      row.last_check_at ? (
        <span className="text-sm text-text-secondary">
          {formatDistanceToNow(new Date(row.last_check_at), { addSuffix: true })}
        </span>
      ) : (
        <span className="text-sm text-text-muted">Never</span>
      ),
  },
  { key: "total_jobs_found", label: "Jobs Found", sortable: true },
  {
    key: "failure_count",
    label: "Failures",
    sortable: true,
    render: (row: SourceHealth) => (
      <span
        className={cn(
          "font-mono text-sm",
          row.failure_count > 0 ? "text-accent-danger" : "text-text-secondary"
        )}
      >
        {row.failure_count}
      </span>
    ),
  },
];

export default function Admin() {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [sortKey, setSortKey] = useState<string | undefined>();
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("asc");

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

  function handleImportClick() {
    fileInputRef.current?.click();
  }

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
        className="hero-panel"
        eyebrow="Operations"
        title="Admin"
        description="System health, diagnostics, source telemetry, and maintenance actions for the data plane."
        meta={
          <>
            <span className="brutal-panel px-3 py-2 font-mono font-bold uppercase tracking-[0.16em]">
              API {health?.status ?? "unknown"}
            </span>
            <span className="brutal-panel px-3 py-2 font-mono font-bold uppercase tracking-[0.16em]">
              DB {dbOnline ? "online" : "offline"}
            </span>
            <span className="brutal-panel px-3 py-2 font-mono font-bold uppercase tracking-[0.16em]">
              {healthySources}/{sources?.length ?? 0} healthy
            </span>
          </>
        }
      />

      <SplitWorkspace
        primary={
          <Surface className="hero-panel">
            <SectionHeader
              title="System Health"
              description="Live service connectivity and environment status."
            />
            {loadingHealth ? (
              <div className="mt-6 grid gap-3 sm:grid-cols-3">
                {Array.from({ length: 3 }).map((_, index) => (
                  <div key={index} className="brutal-panel p-4">
                    <Skeleton variant="text" className="h-4 w-20" />
                    <Skeleton variant="text" className="mt-4 h-6 w-24" />
                  </div>
                ))}
              </div>
            ) : (
              <div className="mt-6 grid gap-3 sm:grid-cols-3">
                <div className="brutal-panel p-4">
                  <p className="font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-text-muted">
                    Database
                  </p>
                  <div className="mt-4">
                    <Badge variant={dbOnline ? "success" : "danger"}>
                      {dbOnline ? "Online" : "Offline"}
                    </Badge>
                  </div>
                </div>
                <div className="brutal-panel p-4">
                  <p className="font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-text-muted">
                    Redis
                  </p>
                  <div className="mt-4">
                    <Badge variant="success">Connected</Badge>
                  </div>
                </div>
                <div className="brutal-panel p-4">
                  <p className="font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-text-muted">
                    API Status
                  </p>
                  <div className="mt-4">
                    <Badge variant={health?.status === "ok" ? "success" : "danger"}>
                      {health?.status ?? "Unknown"}
                    </Badge>
                  </div>
                </div>
              </div>
            )}
          </Surface>
        }
        secondary={
          <Surface className="brutal-panel">
            <SectionHeader
              title="Diagnostics"
              description="Operational counters and environment details surfaced by the backend."
            />
            <div className="mt-6 grid gap-3 sm:grid-cols-2">
              <DiagnosticItem
                icon={<Cloud size={16} weight="bold" />}
                label="Python Version"
                value={diagnostics?.python_version ?? "-"}
                loading={loadingDiagnostics}
              />
              <DiagnosticItem
                icon={<Database size={16} />}
                label="Platform"
                value={runtimePlatform}
                loading={loadingDiagnostics}
              />
              <DiagnosticItem
                icon={<Clock size={16} />}
                label="Applications"
                value={applicationCount}
                loading={loadingDiagnostics}
              />
              <DiagnosticItem
                icon={<Briefcase size={16} weight="bold" />}
                label="Total Jobs"
                value={typeof totalJobs === "number" ? totalJobs.toLocaleString() : totalJobs}
                loading={loadingDiagnostics}
              />
            </div>
          </Surface>
        }
      />

      <Surface padding="none" className="hero-panel">
        <div className="border-b-2 border-border px-5 py-5">
          <SectionHeader
            title="Source Health"
            description="Sortable source telemetry for scraper stability, freshness, and failure tracking."
            action={
              <div className="font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-text-muted">
                {sortedSources.length} sources
              </div>
            }
          />
        </div>

        {loadingSources ? (
          <div className="space-y-0">
            {Array.from({ length: 4 }).map((_, index) => (
              <div
                key={index}
                className="grid gap-3 border-t-2 border-border px-5 py-4 md:grid-cols-[minmax(0,1.5fr)_140px_180px_120px_100px]"
              >
                <Skeleton variant="text" className="h-4 w-24" />
                <Skeleton variant="text" className="h-4 w-20" />
                <Skeleton variant="text" className="h-4 w-24" />
                <Skeleton variant="text" className="h-4 w-16" />
                <Skeleton variant="text" className="h-4 w-12" />
              </div>
            ))}
          </div>
        ) : sortedSources.length === 0 ? (
          <div className="p-5">
            <EmptyState
              icon={<Warning size={40} weight="fill" />}
              title="No sources configured"
              description="Source health data will appear here once scrapers are running."
            />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[44rem]">
              <thead className="bg-[var(--color-bg-tertiary)]">
                <tr className="border-b-2 border-border">
                  {sourceHealthColumns.map((column) => (
                    <th key={column.key} className="px-5 py-3 text-left">
                      {column.sortable ? (
                        <button
                          type="button"
                          onClick={() => handleSort(column.key)}
                          className="font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-text-muted transition-colors hover:text-text-primary"
                        >
                          {column.label}
                          {sortKey === column.key ? ` ${sortOrder === "asc" ? "ASC" : "DESC"}` : ""}
                        </button>
                      ) : (
                        <span className="font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-text-muted">
                          {column.label}
                        </span>
                      )}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {sortedSources.map((row) => (
                  <tr key={row.id} className="border-b-2 border-border last:border-b-0">
                    {sourceHealthColumns.map((column) => (
                      <td key={column.key} className="px-5 py-4 text-sm text-text-primary">
                        {column.render
                          ? column.render(row)
                          : String(row[column.key as keyof SourceHealth] ?? "")}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Surface>

      <Surface className="hero-panel">
        <SectionHeader
          title="Actions"
          description="Maintenance operations for search indexing and workspace data portability."
        />
        <div className="mt-6 flex flex-wrap gap-3">
          <Button
            variant="secondary"
            icon={<ArrowClockwise size={14} weight="bold" />}
            loading={reindexMutation.isPending}
            onClick={() => reindexMutation.mutate()}
          >
            Reindex FTS
          </Button>
          <Button
            variant="secondary"
            icon={<ArrowClockwise size={14} weight="bold" />}
            loading={reindexMutation.isPending}
            onClick={() => reindexMutation.mutate()}
          >
            Reindex Search
          </Button>
          <Button
            variant="secondary"
            icon={<DownloadSimple size={14} weight="bold" />}
            loading={exportMutation.isPending}
            onClick={() => exportMutation.mutate()}
          >
            Export Data
          </Button>
          <Button
            variant="secondary"
            icon={<UploadSimple size={14} weight="bold" />}
            loading={importMutation.isPending}
            onClick={handleImportClick}
          >
            Import Data
          </Button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".json"
            className="hidden"
            onChange={handleFileChange}
          />
        </div>
      </Surface>
    </div>
  );
}
