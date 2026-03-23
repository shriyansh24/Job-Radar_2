import { cva } from "class-variance-authority";

export const buttonVariants = cva(
  "inline-flex items-center justify-center font-medium rounded-[var(--radius-lg)] transition-[background-color,color,transform,border-color,box-shadow] duration-[var(--transition-fast)] disabled:opacity-50 disabled:pointer-events-none active:translate-y-[1px] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-border-focus/25",
  {
    variants: {
      variant: {
        default:
          "bg-accent-primary hover:bg-accent-primary/90 text-white shadow-[var(--shadow-sm)] hover:shadow-[var(--shadow-md)]",
        primary:
          "bg-accent-primary hover:bg-accent-primary/90 text-white shadow-[var(--shadow-sm)] hover:shadow-[var(--shadow-md)]",
        secondary:
          "bg-bg-secondary hover:bg-bg-tertiary text-text-primary border border-border shadow-[var(--shadow-xs)]",
        outline:
          "bg-bg-secondary hover:bg-bg-tertiary text-text-primary border border-border shadow-[var(--shadow-xs)]",
        danger:
          "bg-accent-danger hover:bg-accent-danger/90 text-white shadow-[var(--shadow-sm)]",
        destructive:
          "bg-accent-danger hover:bg-accent-danger/90 text-white shadow-[var(--shadow-sm)]",
        success:
          "bg-accent-success hover:bg-accent-success/90 text-white shadow-[var(--shadow-sm)]",
        ghost:
          "bg-transparent text-text-secondary hover:bg-bg-hover hover:text-text-primary",
        link: "bg-transparent px-0 py-0 text-accent-primary shadow-none hover:text-accent-primary-hover",
      },
      size: {
        default: "px-4 py-2 text-sm gap-2",
        sm: "px-3 py-1.5 text-xs gap-1.5",
        md: "px-4 py-2 text-sm gap-2",
        lg: "px-6 py-2.5 text-base gap-2.5",
      },
    },
    defaultVariants: {
      variant: "primary",
      size: "md",
    },
  }
);
