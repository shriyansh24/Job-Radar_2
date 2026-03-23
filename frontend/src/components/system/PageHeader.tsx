import * as React from "react"

import { cn } from "@/lib/utils"

type PageHeaderProps = React.HTMLAttributes<HTMLDivElement> & {
  eyebrow?: React.ReactNode
  title: React.ReactNode
  description?: React.ReactNode
  meta?: React.ReactNode
  actions?: React.ReactNode
}

function PageHeader({
  className,
  eyebrow,
  title,
  description,
  meta,
  actions,
  ...props
}: PageHeaderProps) {
  return (
    <div
      className={cn(
        "flex flex-col gap-6 border-b border-border/70 px-5 py-5 sm:px-6 sm:py-6",
        className
      )}
      {...props}
    >
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div className="min-w-0 space-y-2">
          {eyebrow ? (
            <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-muted-foreground">
              {eyebrow}
            </p>
          ) : null}
          <div className="space-y-2">
            <h1 className="text-2xl font-semibold tracking-[-0.04em] sm:text-3xl">
              {title}
            </h1>
            {description ? (
              <p className="max-w-3xl text-sm leading-6 text-muted-foreground sm:text-[0.95rem]">
                {description}
              </p>
            ) : null}
          </div>
        </div>

        {actions ? (
          <div className="flex flex-wrap items-center gap-2 lg:justify-end">
            {actions}
          </div>
        ) : null}
      </div>

      {meta ? (
        <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
          {meta}
        </div>
      ) : null}
    </div>
  )
}

export { PageHeader }
export type { PageHeaderProps }
