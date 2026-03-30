import * as React from "react";

import { cn } from "@/lib/utils";

import { Surface } from "./Surface";

type ActivityItem = {
  key: string;
  title: React.ReactNode;
  body?: React.ReactNode;
  meta?: React.ReactNode;
  icon?: React.ReactNode;
};

type ActivityFeedProps = React.HTMLAttributes<HTMLDivElement> & {
  items: ActivityItem[];
  empty?: React.ReactNode;
};

function ActivityFeed({
  className,
  items,
  empty,
  ...props
}: ActivityFeedProps) {
  return (
    <Surface tone="default" padding="none" radius="xl" className={className} {...props}>
      {items.length ? (
        <div className="divide-y divide-border/70">
          {items.map((item) => (
            <div key={item.key} className="flex gap-3 px-5 py-4">
              {item.icon ? (
                <div className="mt-0.5 flex size-9 shrink-0 items-center justify-center rounded-[var(--radius-md)] border border-border/70 bg-background/80 text-muted-foreground">
                  {item.icon}
                </div>
              ) : null}
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="text-sm font-medium text-foreground">{item.title}</div>
                  {item.meta ? (
                    <div className="text-xs text-muted-foreground">{item.meta}</div>
                  ) : null}
                </div>
                {item.body ? (
                  <div className="mt-1.5 text-sm leading-6 text-muted-foreground">
                    {item.body}
                  </div>
                ) : null}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className={cn("px-5 py-10", !empty && "text-sm text-muted-foreground")}>
          {empty ?? "No activity yet."}
        </div>
      )}
    </Surface>
  );
}

export { ActivityFeed };
export type { ActivityFeedProps, ActivityItem };
