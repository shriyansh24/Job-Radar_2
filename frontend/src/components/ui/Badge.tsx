import { cva } from "class-variance-authority";

import { cn } from "../../lib/utils";

interface BadgeProps {
  variant?:
    | "default"
    | "secondary"
    | "outline"
    | "success"
    | "warning"
    | "danger"
    | "info";
  size?: "sm" | "md";
  children: React.ReactNode;
  className?: string;
}

const badgeVariants = cva(
  "inline-flex items-center justify-center gap-1 whitespace-nowrap rounded-none border-2 font-mono font-bold uppercase tracking-[0.18em]",
  {
    variants: {
      variant: {
        default: "border-border bg-card text-foreground",
        secondary:
          "border-border bg-[var(--color-bg-tertiary)] text-text-secondary",
        outline: "border-border bg-transparent text-foreground",
        success:
          "border-border bg-[var(--color-accent-success-subtle)] text-[var(--color-accent-success)]",
        warning:
          "border-border bg-[var(--color-accent-warning-subtle)] text-[var(--color-accent-warning)]",
        danger:
          "border-border bg-[var(--color-accent-danger-subtle)] text-[var(--color-accent-danger)]",
        info:
          "border-border bg-[var(--color-accent-primary-subtle)] text-[var(--color-accent-primary)]",
      },
      size: {
        sm: "px-2 py-1 text-[9px]",
        md: "px-3 py-1.5 text-[10px]",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "sm",
    },
  }
);

export default function Badge({
  variant = "default",
  size = "sm",
  children,
  className,
}: BadgeProps) {
  return (
    <span className={cn(badgeVariants({ variant, size }), className)}>
      {children}
    </span>
  );
}
