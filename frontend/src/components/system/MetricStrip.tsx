import * as React from "react";

import { cn } from "@/lib/utils";

import { Surface } from "./Surface";

type MetricItem = {
  key: string;
  label: React.ReactNode;
  value: React.ReactNode;
  hint?: React.ReactNode;
  icon?: React.ReactNode;
  tone?: "default" | "success" | "warning" | "danger";
};

type MetricStripProps = React.HTMLAttributes<HTMLDivElement> & {
  items: MetricItem[];
};

const accentClasses: Record<NonNullable<MetricItem["tone"]>, string> = {
  default: "bg-card",
  success: "bg-[var(--color-accent-secondary-subtle)]",
  warning: "bg-[var(--color-accent-warning-subtle)]",
  danger: "bg-[var(--color-accent-danger-subtle)]",
};

function metricValueClass(value: React.ReactNode): string {
  if (typeof value === "number") {
    return "mono-num mt-4 text-4xl font-bold text-foreground";
  }

  if (typeof value === "string") {
    const trimmed = value.trim();
    const numericLike = /^[\d$.,%kKxX:+/-]+$/.test(trimmed);

    if (numericLike && trimmed.length <= 14) {
      return "mono-num mt-4 text-4xl font-bold text-foreground";
    }

    if (trimmed.length <= 14) {
      return "mt-4 text-3xl font-black uppercase tracking-[-0.05em] text-foreground";
    }

    if (trimmed.length <= 20) {
      return "mt-4 break-all text-lg font-semibold leading-tight text-foreground sm:text-xl";
    }

    return "mt-4 break-all text-sm font-semibold leading-6 text-foreground sm:text-base";
  }

  return "mt-4 text-3xl font-black tracking-[-0.05em] text-foreground";
}

function MetricStrip({ className, items, ...props }: MetricStripProps) {
  return (
    <div
      className={cn("grid gap-4 md:grid-cols-2 xl:grid-cols-4", className)}
      {...props}
    >
      {items.map((item) => (
        <Surface
          key={item.key}
          tone="default"
          padding="lg"
          radius="xl"
          className={cn("min-w-0", accentClasses[item.tone ?? "default"])}
        >
          <div className="flex items-start justify-between gap-4">
            <div className="min-w-0">
              <div className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
                {item.label}
              </div>
              <div className={metricValueClass(item.value)}>
                {item.value}
              </div>
              {item.hint ? (
                <p className="mt-3 text-sm leading-6 text-muted-foreground">
                  {item.hint}
                </p>
              ) : null}
            </div>
            {item.icon ? (
              <div className="flex size-11 shrink-0 items-center justify-center border-2 border-border bg-background text-muted-foreground shadow-[var(--shadow-xs)]">
                {item.icon}
              </div>
            ) : null}
          </div>
        </Surface>
      ))}
    </div>
  );
}

export { MetricStrip };
export type { MetricItem, MetricStripProps };
