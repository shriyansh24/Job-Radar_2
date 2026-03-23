import * as React from "react"

import { cn } from "@/lib/utils"

type WorkspaceShellProps = React.HTMLAttributes<HTMLDivElement> & {
  sidebar?: React.ReactNode
  header?: React.ReactNode
  rail?: React.ReactNode
  contentClassName?: string
  layout?: "full" | "sidebar" | "sidebar-rail"
}

const layoutClasses: Record<
  NonNullable<WorkspaceShellProps["layout"]>,
  string
> = {
  full: "grid-cols-1",
  sidebar: "lg:grid-cols-[280px_minmax(0,1fr)]",
  "sidebar-rail": "xl:grid-cols-[280px_minmax(0,1fr)_320px]",
}

function WorkspaceShell({
  className,
  sidebar,
  header,
  rail,
  children,
  contentClassName,
  layout = rail ? "sidebar-rail" : sidebar ? "sidebar" : "full",
  ...props
}: WorkspaceShellProps) {
  return (
    <div
      className={cn(
        "min-h-[100dvh] bg-background text-foreground",
        className
      )}
      {...props}
    >
      <div className={cn("grid min-h-[100dvh]", layoutClasses[layout])}>
        {sidebar ? (
          <aside className="border-b border-border/70 bg-background/95 lg:border-r lg:border-b-0">
            {sidebar}
          </aside>
        ) : null}

        <div className="flex min-w-0 flex-col">
          {header ? (
            <header className="sticky top-0 z-20 border-b border-border/70 bg-background/88 backdrop-blur-xl">
              {header}
            </header>
          ) : null}

          <main className={cn("min-w-0 flex-1", contentClassName)}>
            {children}
          </main>
        </div>

        {rail ? (
          <aside className="hidden border-l border-border/70 bg-background/92 xl:block">
            {rail}
          </aside>
        ) : null}
      </div>
    </div>
  )
}

export { WorkspaceShell }
export type { WorkspaceShellProps }
