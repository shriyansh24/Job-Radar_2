import * as React from "react"

import { cn } from "@/lib/utils"

type SplitWorkspaceProps = React.HTMLAttributes<HTMLDivElement> & {
  primary: React.ReactNode
  secondary?: React.ReactNode
  tertiary?: React.ReactNode
}

function SplitWorkspace({
  className,
  primary,
  secondary,
  tertiary,
  ...props
}: SplitWorkspaceProps) {
  return (
    <div
      className={cn(
        "grid gap-6 xl:grid-cols-[minmax(0,1.25fr)_minmax(0,0.95fr)]",
        tertiary && "2xl:grid-cols-[minmax(0,1.2fr)_minmax(0,0.9fr)_280px]",
        className
      )}
      {...props}
    >
      <div className="min-w-0 space-y-6">{primary}</div>
      {secondary ? <div className="min-w-0 space-y-4">{secondary}</div> : null}
      {tertiary ? <div className="min-w-0">{tertiary}</div> : null}
    </div>
  )
}

export { SplitWorkspace }
export type { SplitWorkspaceProps }
