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
        "grid gap-6 xl:grid-cols-[minmax(0,1.45fr)_minmax(340px,1fr)]",
        tertiary && "2xl:grid-cols-[minmax(0,1.35fr)_minmax(340px,1fr)_280px]",
        className
      )}
      {...props}
    >
      <div className="min-w-0">{primary}</div>
      {secondary ? <div className="min-w-0">{secondary}</div> : null}
      {tertiary ? <div className="min-w-0">{tertiary}</div> : null}
    </div>
  )
}

export { SplitWorkspace }
export type { SplitWorkspaceProps }
