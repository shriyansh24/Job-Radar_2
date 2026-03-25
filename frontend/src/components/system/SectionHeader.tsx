import * as React from "react"

import { cn } from "@/lib/utils"

type SectionHeaderProps = React.HTMLAttributes<HTMLDivElement> & {
  title: React.ReactNode
  description?: React.ReactNode
  action?: React.ReactNode
}

function SectionHeader({
  className,
  title,
  description,
  action,
  ...props
}: SectionHeaderProps) {
  return (
    <div
      className={cn(
        "flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between",
        className
      )}
      {...props}
    >
      <div className="space-y-1">
        <h2 className="text-xl font-black uppercase tracking-[-0.05em]">{title}</h2>
        {description ? (
          <p className="text-sm leading-6 text-muted-foreground">{description}</p>
        ) : null}
      </div>

      {action ? <div className="shrink-0">{action}</div> : null}
    </div>
  )
}

export { SectionHeader }
export type { SectionHeaderProps }
