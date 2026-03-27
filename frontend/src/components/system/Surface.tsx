import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const surfaceVariants = cva(
  "relative rounded-none border-2 border-border text-card-foreground transition-[border-color,background-color,box-shadow,transform] duration-[var(--transition-normal)]",
  {
    variants: {
      tone: {
        default: "bg-card shadow-none",
        subtle: "bg-[var(--color-bg-secondary)] shadow-none",
        elevated: "bg-[var(--color-bg-secondary)] shadow-[var(--shadow-hard-sm)]",
        ghost: "border-transparent bg-transparent shadow-none",
      },
      padding: {
        none: "",
        sm: "p-4",
        md: "p-5 sm:p-6",
        lg: "p-6 sm:p-8",
      },
      radius: {
        md: "rounded-none",
        lg: "rounded-none",
        xl: "rounded-none",
      },
      interactive: {
        true: "card-hover cursor-pointer",
        false: "",
      },
    },
    defaultVariants: {
      tone: "default",
      padding: "md",
      radius: "lg",
      interactive: false,
    },
  }
)

type SurfaceProps = React.HTMLAttributes<HTMLDivElement> &
  VariantProps<typeof surfaceVariants>

function Surface({
  className,
  tone,
  padding,
  radius,
  interactive,
  ...props
}: SurfaceProps) {
  return (
    <div
      className={cn(
        surfaceVariants({ tone, padding, radius, interactive }),
        className
      )}
      {...props}
    />
  )
}

export { Surface }
export type { SurfaceProps }
