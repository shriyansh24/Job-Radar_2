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
        "border-2 border-border bg-secondary px-5 py-5 shadow-[var(--shadow-lg)] sm:px-6 sm:py-7",
        className
      )}
      {...props}
    >
      <div className="flex flex-col gap-6 xl:flex-row xl:items-start xl:justify-between">
        <div className="min-w-0 space-y-4">
          <div className="flex flex-wrap items-center gap-2">
            {eyebrow ? (
              <p className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
                {eyebrow}
              </p>
            ) : null}
            {meta ? (
              <div className="flex flex-wrap items-center gap-2 border-l-2 border-border pl-2">
                {meta}
              </div>
            ) : null}
          </div>
          <div className="space-y-3">
            <h1 className="font-display text-[clamp(2.2rem,4vw,3.9rem)] font-black uppercase leading-[0.92] tracking-[-0.06em] text-text-primary">
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

    </div>
  )
}

export { PageHeader }
export type { PageHeaderProps }
