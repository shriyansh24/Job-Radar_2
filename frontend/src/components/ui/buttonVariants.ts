import { cva } from "class-variance-authority";

export const buttonVariants = cva(
  "hard-press inline-flex items-center justify-center gap-2 border-2 border-border font-sans font-black uppercase tracking-[0.12em] transition-[background-color,color,transform,border-color,box-shadow] duration-[var(--transition-fast)] disabled:pointer-events-none disabled:opacity-50 focus-visible:outline-none focus-visible:ring-0",
  {
    variants: {
      variant: {
        default:
          "bg-primary text-primary-foreground",
        primary:
          "bg-primary text-primary-foreground",
        secondary:
          "bg-background text-foreground",
        outline:
          "bg-background text-foreground",
        danger:
          "bg-[var(--color-accent-danger)] text-white",
        destructive:
          "bg-[var(--color-accent-danger)] text-white",
        success: "bg-[var(--color-accent-success)] text-white",
        ghost:
          "border-transparent bg-transparent text-text-secondary shadow-none hover:border-border hover:bg-[var(--color-bg-secondary)] hover:text-foreground",
        link:
          "border-transparent bg-transparent px-0 py-0 text-[var(--color-accent-primary)] shadow-none hover:text-[var(--color-accent-primary-hover)]",
      },
      size: {
        default: "px-4 py-2.5 text-[11px]",
        sm: "px-3 py-2 text-[10px]",
        md: "px-4 py-2.5 text-[11px]",
        lg: "px-6 py-3 text-[12px]",
      },
    },
    defaultVariants: {
      variant: "primary",
      size: "md",
    },
  }
);
