import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const stateBlockVariants = cva("border-2", {
  variants: {
    tone: {
      neutral: "border-border bg-card",
      muted: "border-border bg-[var(--color-bg-tertiary)]",
      success:
        "border-border bg-[var(--color-accent-secondary-subtle)]",
      warning:
        "border-border bg-[var(--color-accent-warning-subtle)]",
      danger: "border-border bg-[var(--color-accent-danger-subtle)]",
    },
  },
  defaultVariants: {
    tone: "neutral",
  },
})

type StateBlockProps = React.HTMLAttributes<HTMLDivElement> &
  VariantProps<typeof stateBlockVariants> & {
    icon?: React.ReactNode
    title: React.ReactNode
    description?: React.ReactNode
    action?: React.ReactNode
  }

function StateBlock({
  className,
  tone,
  icon,
  title,
  description,
  action,
  ...props
}: StateBlockProps) {
  return (
    <div
      className={cn(
        "border-2 p-5 shadow-[var(--shadow-sm)]",
        stateBlockVariants({ tone }),
        className
      )}
      {...props}
    >
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex min-w-0 gap-3">
          {icon ? (
            <div className="flex size-10 shrink-0 items-center justify-center border-2 border-border bg-background text-muted-foreground shadow-[var(--shadow-xs)]">
              {icon}
            </div>
          ) : null}
          <div className="min-w-0 space-y-1.5">
            <h3 className="font-mono text-[11px] font-bold uppercase tracking-[0.18em]">{title}</h3>
            {description ? (
              <p className="text-sm leading-6 text-muted-foreground">
                {description}
              </p>
            ) : null}
          </div>
        </div>
        {action ? <div className="shrink-0">{action}</div> : null}
      </div>
    </div>
  )
}

export { StateBlock }
export type { StateBlockProps }
