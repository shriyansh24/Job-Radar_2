import {
  ArrowsDownUp,
  ArrowDown,
  ArrowUp,
} from "@phosphor-icons/react";
import { cn } from "../../lib/utils";

interface Column<T> {
  key: string;
  label: string;
  sortable?: boolean;
  render?: (row: T) => React.ReactNode;
  className?: string;
}

interface TableProps<T> {
  columns: Column<T>[];
  data: T[];
  sortKey?: string;
  sortOrder?: 'asc' | 'desc';
  onSort?: (key: string) => void;
  onRowClick?: (row: T) => void;
  className?: string;
}

export default function Table<T extends Record<string, unknown>>({
  columns,
  data,
  sortKey,
  sortOrder,
  onSort,
  onRowClick,
  className,
}: TableProps<T>) {
  return (
    <div className={cn("overflow-x-auto border-2 border-border bg-card shadow-[var(--shadow-sm)]", className)}>
      <table className="w-full">
        <thead>
          <tr className="border-b-2 border-border bg-[var(--color-bg-tertiary)]">
            {columns.map((col) => (
              <th
                key={col.key}
                className={cn(
                  "px-4 py-3 text-left font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-text-muted",
                  col.sortable && "cursor-pointer hover:text-text-secondary",
                  col.className
                )}
                onClick={() => col.sortable && onSort?.(col.key)}
              >
                <span className="flex items-center gap-1">
                  {col.label}
                  {col.sortable && (
                    sortKey === col.key ? (
                      sortOrder === "asc" ? (
                        <ArrowUp size={14} weight="bold" />
                      ) : (
                        <ArrowDown size={14} weight="bold" />
                      )
                    ) : (
                      <ArrowsDownUp size={14} weight="bold" className="opacity-40" />
                    )
                  )}
                </span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, i) => (
            <tr
              key={i}
              className={cn(
                "border-b-2 border-border/20 transition-colors last:border-b-0",
                onRowClick && "cursor-pointer hover:bg-[var(--color-bg-hover)]"
              )}
              onClick={() => onRowClick?.(row)}
            >
              {columns.map((col) => (
                <td
                  key={col.key}
                  className={cn("px-4 py-3 text-sm text-text-primary", col.className)}
                >
                  {col.render ? col.render(row) : String(row[col.key] ?? "")}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
