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
        "border-2 border-border bg-card px-5 py-5 shadow-[var(--shadow-sm)] sm:px-6 sm:py-6",
        className
      )}
      {...props}
    >
      <div className="flex flex-col gap-5 xl:flex-row xl:items-end xl:justify-between">
        <div className="min-w-0 space-y-3">
          {eyebrow ? (
            <p className="font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
              {eyebrow}
            </p>
          ) : null}
          <div className="space-y-3">
            <h1 className="heading-page text-text-primary">
              {title}
            </h1>
            {description ? (
              <p className="max-w-3xl text-sm leading-6 text-muted-foreground sm:text-base">
                {description}
              </p>
            ) : null}
          </div>
        </div>

        {actions ? (
          <div className="flex flex-wrap items-center gap-2 xl:justify-end">
            {actions}
          </div>
        ) : null}
      </div>

      {meta ? (
        <div className="flex flex-wrap items-center gap-2 border-t-2 border-border pt-4 text-xs text-muted-foreground">
          {meta}
        </div>
      ) : null}
    </div>
  )
}

export { PageHeader }
export type { PageHeaderProps }
