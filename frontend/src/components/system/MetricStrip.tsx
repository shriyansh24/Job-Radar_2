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
  default: "border-border/70",
  success: "border-[var(--color-accent-success)]/30",
  warning: "border-[var(--color-accent-warning)]/30",
  danger: "border-[var(--color-accent-danger)]/30",
};

function MetricStrip({ className, items, ...props }: MetricStripProps) {
  return (
    <div
      className={cn("grid gap-3 sm:grid-cols-2 xl:grid-cols-4", className)}
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
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <div className="text-[11px] font-medium uppercase tracking-[0.18em] text-muted-foreground">
                {item.label}
              </div>
              <div className="mt-2 text-2xl font-semibold tracking-[-0.04em] text-foreground">
                {item.value}
              </div>
              {item.hint ? (
                <p className="mt-2 text-sm leading-6 text-muted-foreground">
                  {item.hint}
                </p>
              ) : null}
            </div>
            {item.icon ? (
              <div className="flex size-10 shrink-0 items-center justify-center rounded-[var(--radius-lg)] border border-border/70 bg-background/75 text-muted-foreground">
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
