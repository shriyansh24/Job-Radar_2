import { TrendDown, TrendUp } from "@phosphor-icons/react";
import { clsx } from "clsx";

interface StatCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  change?: { value: number; positive: boolean };
  className?: string;
}

export default function StatCard({ title, value, icon, change, className }: StatCardProps) {
  return (
    <div
      className={clsx(
        "border-2 border-border bg-card p-5 shadow-[var(--shadow-sm)]",
        className
      )}
    >
      <div className="flex items-center justify-between mb-3">
        <span className="command-label">{title}</span>
        <span className="text-text-muted">{icon}</span>
      </div>
      <div className="flex items-end gap-3">
        <span className="mono-num text-3xl font-bold text-text-primary">
          {value}
        </span>
        {change && (
          <span
            className={clsx(
              "flex items-center gap-1 text-sm font-medium",
              change.positive ? "text-accent-success" : "text-accent-danger"
            )}
          >
            {change.positive ? (
              <TrendUp size={14} weight="bold" />
            ) : (
              <TrendDown size={14} weight="bold" />
            )}
            {change.positive ? "+" : ""}
            {change.value}%
          </span>
        )}
      </div>
    </div>
  );
}
