import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

import { Surface } from "./Surface"

const stateBlockVariants = cva("border-l-2", {
  variants: {
    tone: {
      neutral: "border-l-border",
      muted: "border-l-muted bg-muted/40",
      success:
        "border-l-[var(--color-accent-success)] bg-[var(--color-accent-success-subtle)]",
      warning:
        "border-l-[var(--color-accent-warning)] bg-[var(--color-accent-warning-subtle)]",
      danger: "border-l-destructive bg-destructive/10",
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
    <Surface
      tone="default"
      padding="md"
      radius="lg"
      className={cn(stateBlockVariants({ tone }), className)}
      {...props}
    >
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex min-w-0 gap-3">
          {icon ? (
            <div className="flex size-10 shrink-0 items-center justify-center rounded-[var(--radius-md)] bg-background/80 text-muted-foreground">
              {icon}
            </div>
          ) : null}
          <div className="min-w-0 space-y-1.5">
            <h3 className="text-sm font-semibold tracking-[-0.01em]">{title}</h3>
            {description ? (
              <p className="text-sm leading-6 text-muted-foreground">
                {description}
              </p>
            ) : null}
          </div>
        </div>
        {action ? <div className="shrink-0">{action}</div> : null}
      </div>
    </Surface>
  )
}

export { StateBlock }
export type { StateBlockProps }
