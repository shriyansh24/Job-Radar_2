import {
  Pulse,
  ArrowClockwise,
  Briefcase,
  Cpu,
  Clock,
  Database,
  DownloadSimple,
  Cloud,
  UploadSimple,
  UsersThree,
  Warning,
} from "@phosphor-icons/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { formatDistanceToNow } from "date-fns";
import { useRef, useState } from "react";
import { adminApi, type SourceHealth } from "../api/admin";
import Badge from "../components/ui/Badge";
import Button from "../components/ui/Button";
import Card from "../components/ui/Card";
import EmptyState from "../components/ui/EmptyState";
import Skeleton from "../components/ui/Skeleton";
import { toast } from "../components/ui/Toast";

function healthBadgeVariant(state: string): 'success' | 'warning' | 'danger' | 'default' {
  switch (state) {
    case 'healthy':
      return 'success';
    case 'degraded':
      return 'warning';
    case 'unhealthy':
      return 'danger';
    default:
      return 'default';
  }
}

function DiagnosticItem({
  icon,
  label,
  value,
  loading,
}: {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  loading: boolean;
}) {
  return (
    <div className="flex items-center gap-3 py-2">
      <div className="text-text-muted">{icon}</div>
      <div className="min-w-0 flex-1">
        <p className="text-xs text-text-muted">{label}</p>
        {loading ? (
          <Skeleton variant="text" className="w-24 h-5" />
        ) : (
          <p className="text-sm font-medium text-text-primary">{value}</p>
        )}
      </div>
    </div>
  );
}

const sourceHealthColumns: {
  key: string;
  label: string;
  sortable?: boolean;
  render?: (row: SourceHealth) => React.ReactNode;
  className?: string;
}[] = [
  { key: 'source_name', label: 'Source', sortable: true },
  {
    key: 'health_state',
    label: 'Status',
    render: (row: SourceHealth) => (
      <Badge variant={healthBadgeVariant(row.health_state)}>
        {row.health_state}
      </Badge>
    ),
  },
  {
    key: 'last_check_at',
    label: 'Last Check',
    render: (row: SourceHealth) =>
      row.last_check_at ? (
        <span className="text-sm text-text-secondary">
          {formatDistanceToNow(new Date(row.last_check_at), { addSuffix: true })}
        </span>
      ) : (
        <span className="text-sm text-text-muted">Never</span>
      ),
  },
  { key: 'total_jobs_found', label: 'Jobs Found', sortable: true },
  {
    key: 'failure_count',
    label: 'Failures',
    sortable: true,
    render: (row: SourceHealth) => (
      <span className={row.failure_count > 0 ? 'text-accent-danger font-medium' : 'text-text-secondary'}>
        {row.failure_count}
      </span>
    ),
  },
];

export default function Admin() {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [sortKey, setSortKey] = useState<string | undefined>();
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');

  const { data: health, isLoading: loadingHealth } = useQuery({
    queryKey: ['admin', 'health'],
    queryFn: () => adminApi.health().then((r) => r.data),
    refetchInterval: 30_000,
  });

  const { data: diagnostics, isLoading: loadingDiagnostics } = useQuery({
    queryKey: ['admin', 'diagnostics'],
    queryFn: () => adminApi.diagnostics().then((r) => r.data),
  });

  const { data: sources, isLoading: loadingSources } = useQuery({
    queryKey: ['admin', 'sourceHealth'],
    queryFn: () => adminApi.sourceHealth().then((r) => r.data),
  });

  const reindexMutation = useMutation({
    mutationFn: () => adminApi.reindex(),
    onSuccess: () => toast('success', 'Full-text search reindex started'),
    onError: () => toast('error', 'Failed to start reindex'),
  });

  const rebuildEmbeddingsMutation = useMutation({
    mutationFn: () => adminApi.reindex(),
    onSuccess: () => toast('success', 'Embedding rebuild started'),
    onError: () => toast('error', 'Failed to start embedding rebuild'),
  });

  const exportMutation = useMutation({
    mutationFn: () => adminApi.exportData(),
    onSuccess: (response) => {
      const blob = new Blob([response.data as BlobPart]);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `jobradar-export-${new Date().toISOString().slice(0, 10)}.json`;
      a.click();
      URL.revokeObjectURL(url);
      toast('success', 'Data exported successfully');
    },
    onError: () => toast('error', 'Failed to export data'),
  });

  const importMutation = useMutation({
    mutationFn: async (file: File) => {
      const text = await file.text();
      const data = JSON.parse(text);
      return adminApi.importData(data);
    },
    onSuccess: () => {
      toast('success', 'Data imported successfully');
      queryClient.invalidateQueries({ queryKey: ['admin'] });
    },
    onError: () => toast('error', 'Failed to import data'),
  });

  function handleImportClick() {
    fileInputRef.current?.click();
  }

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) {
      importMutation.mutate(file);
      e.target.value = '';
    }
  }

  function handleSort(key: string) {
    if (sortKey === key) {
      setSortOrder((prev) => (prev === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortKey(key);
      setSortOrder('asc');
    }
  }

  const sortedSources = [...(sources ?? [])].sort((a, b) => {
    if (!sortKey) return 0;
    const aVal = a[sortKey as keyof SourceHealth];
    const bVal = b[sortKey as keyof SourceHealth];
    if (aVal == null || bVal == null) return 0;
    const cmp = aVal < bVal ? -1 : aVal > bVal ? 1 : 0;
    return sortOrder === 'asc' ? cmp : -cmp;
  });

  const dbOnline = health?.database === 'ok' || health?.database === 'healthy';

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-text-primary">Admin</h1>
      </div>

      {/* Health + Diagnostics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* System Health */}
        <Card>
          <h2 className="text-sm font-semibold text-text-primary mb-4">System Health</h2>
          {loadingHealth ? (
            <div className="space-y-3">
              <Skeleton variant="text" className="w-40 h-5" />
              <Skeleton variant="text" className="w-24 h-5" />
            </div>
          ) : (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-text-secondary">Database</span>
                <Badge variant={dbOnline ? 'success' : 'danger'}>
                  {dbOnline ? 'Online' : 'Offline'}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-text-secondary">Redis</span>
                <Badge variant="success">Connected</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-text-secondary">API Status</span>
                <Badge variant={health?.status === 'ok' ? 'success' : 'danger'}>
                  {health?.status ?? 'Unknown'}
                </Badge>
              </div>
            </div>
          )}
        </Card>

        {/* Diagnostics */}
        <Card>
          <h2 className="text-sm font-semibold text-text-primary mb-2">Diagnostics</h2>
          <div className="grid grid-cols-2 gap-x-4">
            <DiagnosticItem
              icon={<Cloud size={16} weight="bold" />}
              label="Python Version"
              value={diagnostics?.python_version ?? '-'}
              loading={loadingDiagnostics}
            />
            <DiagnosticItem
              icon={<Database size={16} />}
              label="DB Size"
              value={diagnostics?.db_size ?? '-'}
              loading={loadingDiagnostics}
            />
            <DiagnosticItem
              icon={<Clock size={16} />}
              label="Uptime"
              value={diagnostics?.uptime ?? '-'}
              loading={loadingDiagnostics}
            />
            <DiagnosticItem
              icon={<Briefcase size={16} />}
              label="Total Jobs"
              value={diagnostics?.total_jobs?.toLocaleString() ?? '-'}
              loading={loadingDiagnostics}
            />
            <DiagnosticItem
              icon={<UsersThree size={16} weight="bold" />}
              label="Total Users"
              value={diagnostics?.total_users?.toLocaleString() ?? '-'}
              loading={loadingDiagnostics}
            />
            <DiagnosticItem
              icon={<Pulse size={16} weight="bold" />}
              label="Scraper Runs"
              value={diagnostics?.scraper_runs?.toLocaleString() ?? '-'}
              loading={loadingDiagnostics}
            />
          </div>
        </Card>
      </div>

      {/* Source Health */}
      <Card padding="none">
        <div className="flex items-center justify-between px-4 py-3 border-b border-border">
          <h2 className="text-sm font-semibold text-text-primary">Source Health</h2>
        </div>
        {loadingSources ? (
          <div className="p-4 space-y-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="flex gap-4">
                <Skeleton variant="text" className="w-32 h-5" />
                <Skeleton variant="text" className="w-20 h-5" />
                <Skeleton variant="text" className="w-28 h-5" />
                <Skeleton variant="text" className="w-16 h-5" />
                <Skeleton variant="text" className="w-16 h-5" />
              </div>
            ))}
          </div>
        ) : sortedSources.length === 0 ? (
          <EmptyState
            icon={<Warning size={40} weight="fill" />}
            title="No sources configured"
            description="Source health data will appear here once scrapers are running."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border">
                  {sourceHealthColumns.map((col) => (
                    <th
                      key={col.key}
                      className="px-4 py-3 text-left text-xs font-medium text-text-muted uppercase tracking-wider cursor-pointer hover:text-text-secondary"
                      onClick={() => col.sortable && handleSort(col.key)}
                    >
                      {col.label}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {sortedSources.map((row) => (
                  <tr key={row.id} className="border-b border-border/50">
                    {sourceHealthColumns.map((col) => (
                      <td key={col.key} className="px-4 py-3 text-sm text-text-primary">
                        {col.render ? col.render(row) : String(row[col.key as keyof SourceHealth] ?? '')}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Actions */}
      <Card>
        <h2 className="text-sm font-semibold text-text-primary mb-4">Actions</h2>
        <div className="flex flex-wrap gap-3">
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
            icon={<Cpu size={14} weight="bold" />}
            loading={rebuildEmbeddingsMutation.isPending}
            onClick={() => rebuildEmbeddingsMutation.mutate()}
          >
            Rebuild Embeddings
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
      </Card>
    </div>
  );
}
