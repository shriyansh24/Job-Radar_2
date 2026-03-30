import { cva } from "class-variance-authority";

export const buttonVariants = cva(
  "hard-press inline-flex min-h-11 items-center justify-center gap-2 border-2 border-border px-4 py-2.5 font-mono text-[10px] font-bold uppercase tracking-[0.18em] transition-[background-color,color,transform,border-color] duration-[var(--transition-fast)] disabled:pointer-events-none disabled:opacity-50 focus-visible:outline-none focus-visible:ring-0 aria-invalid:border-[var(--color-accent-danger)]",
  {
    variants: {
      variant: {
        default: "bg-card text-foreground shadow-none",
        primary:
          "bg-primary text-primary-foreground shadow-none hover:border-[var(--color-accent-primary)]",
        secondary:
          "bg-card text-foreground shadow-none hover:bg-[var(--color-bg-tertiary)]",
        outline:
          "bg-transparent text-foreground shadow-none hover:bg-[var(--color-bg-secondary)]",
        danger:
          "bg-[var(--color-accent-danger)] text-white shadow-none hover:border-[var(--color-accent-danger)]",
        destructive:
          "bg-[var(--color-accent-danger)] text-white shadow-none hover:border-[var(--color-accent-danger)]",
        success:
          "bg-[var(--color-accent-success)] text-white shadow-none hover:border-[var(--color-accent-success)]",
        warning:
          "bg-[var(--color-accent-warning)] text-[var(--color-text-primary)] shadow-none hover:border-[var(--color-accent-warning)]",
        info:
          "bg-[var(--color-accent-primary)] text-primary-foreground shadow-none hover:border-[var(--color-accent-primary)]",
        ghost:
          "border-transparent bg-transparent px-3 py-2 text-text-secondary shadow-none hover:border-border hover:bg-[var(--color-bg-secondary)] hover:text-foreground",
        link:
          "border-transparent bg-transparent px-0 py-0 text-[var(--color-accent-primary)] shadow-none hover:text-[var(--color-accent-primary-hover)]",
      },
      size: {
        default: "min-h-11 px-4 py-2.5 text-[10px]",
        sm: "min-h-9 px-3 py-2 text-[9px]",
        md: "min-h-11 px-4 py-2.5 text-[10px]",
        lg: "min-h-12 px-6 py-3 text-[11px]",
        icon: "size-11 px-0 py-0",
      },
    },
    defaultVariants: {
      variant: "primary",
      size: "md",
    },
  }
);
