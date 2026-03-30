import type { ReactNode } from "react";
import Skeleton from "../ui/Skeleton";

export function AdminDiagnosticCard({
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
    <div className="border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-secondary)] px-4 py-4">
      <div className="flex items-start gap-3">
        <div className="mt-0.5 text-text-muted">{icon}</div>
        <div className="min-w-0 flex-1">
          <p className="font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-text-muted">{label}</p>
          {loading ? (
            <Skeleton variant="text" className="mt-3 h-5 w-24" />
          ) : (
            <p className="mt-3 text-lg font-black uppercase tracking-[-0.04em] text-text-primary">{value}</p>
          )}
        </div>
      </div>
    </div>
  );
}
