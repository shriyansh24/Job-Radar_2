import * as React from "react"

import { cn } from "@/lib/utils"

import { Surface } from "./Surface"

type CommandBarProps = React.HTMLAttributes<HTMLDivElement> & {
  leading?: React.ReactNode
  trailing?: React.ReactNode
}

function CommandBar({
  className,
  leading,
  trailing,
  children,
  ...props
}: CommandBarProps) {
  return (
    <Surface
      tone="subtle"
      padding="sm"
      radius="lg"
      className={cn(
        "flex flex-col gap-3 border-border/70 bg-background/75 sm:flex-row sm:items-center sm:justify-between",
        className
      )}
      {...props}
    >
      <div className="flex min-w-0 flex-1 items-center gap-3">
        {leading ? <div className="shrink-0">{leading}</div> : null}
        <div className="min-w-0 flex-1">{children}</div>
      </div>
      {trailing ? (
        <div className="flex shrink-0 items-center gap-2">{trailing}</div>
      ) : null}
    </Surface>
  )
}

export { CommandBar }
export type { CommandBarProps }
