import { formatDistanceToNow } from "date-fns";
import type { ReactNode } from "react";
import type { SourceHealth } from "../../api/admin";
import Badge from "../ui/Badge";
import EmptyState from "../ui/EmptyState";
import Skeleton from "../ui/Skeleton";
import { Surface } from "../system/Surface";
import { cn } from "../../lib/utils";

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

const columns: {
  key: string;
  label: string;
  sortable?: boolean;
  render?: (row: SourceHealth) => ReactNode;
}[] = [
  { key: "source_name", label: "Source", sortable: true },
  {
    key: "health_state",
    label: "Status",
    render: (row: SourceHealth) => <Badge variant={healthBadgeVariant(row.health_state)}>{row.health_state}</Badge>,
  },
  {
    key: "last_check_at",
    label: "Last check",
    render: (row: SourceHealth) =>
      row.last_check_at ? (
        <span className="text-sm text-text-secondary">
          {formatDistanceToNow(new Date(row.last_check_at), { addSuffix: true })}
        </span>
      ) : (
        <span className="text-sm text-text-muted">Never</span>
      ),
  },
  { key: "total_jobs_found", label: "Jobs found", sortable: true },
  {
    key: "failure_count",
    label: "Failures",
    sortable: true,
    render: (row: SourceHealth) => (
      <span className={cn("font-mono text-sm", row.failure_count > 0 ? "text-accent-danger" : "text-text-secondary")}>
        {row.failure_count}
      </span>
    ),
  },
];

export function AdminSourceHealthTable({
  loading,
  sortedSources,
  sourceCount,
  sortKey,
  sortOrder,
  onSort,
}: {
  loading: boolean;
  sortedSources: SourceHealth[];
  sourceCount: number;
  sortKey: string | undefined;
  sortOrder: "asc" | "desc";
  onSort: (key: string) => void;
}) {
  return (
    <Surface padding="none" className="border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-secondary)]">
      <div className="border-b-2 border-border px-5 py-5">
        <div className="flex items-start justify-between gap-3">
          <div>
            <div className="text-sm font-bold uppercase tracking-[0.2em]">Source health</div>
            <p className="mt-1 text-sm text-text-secondary">Sortable source telemetry for scraper stability and freshness.</p>
          </div>
          <div className="font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-text-muted">
            {sourceCount} sources
          </div>
        </div>
      </div>

      {loading ? (
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
          <EmptyState title="No sources configured" description="Source health data will appear here once scrapers are running." />
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[44rem]">
            <thead className="bg-[var(--color-bg-tertiary)]">
              <tr className="border-b-2 border-border">
                {columns.map((column) => (
                  <th key={column.key} className="px-5 py-3 text-left">
                    {column.sortable ? (
                      <button
                        type="button"
                        onClick={() => onSort(column.key)}
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
                  {columns.map((column) => (
                    <td key={column.key} className="px-5 py-4 text-sm text-text-primary">
                      {column.render ? column.render(row) : String(row[column.key as keyof SourceHealth] ?? "")}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Surface>
  );
}
