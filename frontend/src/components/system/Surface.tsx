import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const surfaceVariants = cva(
  "relative border border-border/70 text-card-foreground transition-[border-color,background-color,box-shadow,transform] duration-200",
  {
    variants: {
      tone: {
        default: "bg-card shadow-sm",
        subtle: "bg-background/80 shadow-none",
        elevated:
          "bg-card shadow-[var(--shadow-md)] supports-[backdrop-filter]:bg-card/95",
        ghost: "border-transparent bg-transparent shadow-none",
      },
      padding: {
        none: "",
        sm: "p-3",
        md: "p-4 sm:p-5",
        lg: "p-5 sm:p-6",
      },
      radius: {
        md: "rounded-[var(--radius-md)]",
        lg: "rounded-[var(--radius-lg)]",
        xl: "rounded-[var(--radius-xl)]",
      },
      interactive: {
        true: "hover:border-border hover:shadow-[var(--shadow-card-hover)]",
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
