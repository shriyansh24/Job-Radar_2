import type React from "react";
import { SpinnerGap } from "@phosphor-icons/react";
import { motion } from "framer-motion";
import { cn } from "../../lib/utils";

type ButtonDomProps = Omit<
  React.ButtonHTMLAttributes<HTMLButtonElement>,
  | "onDrag"
  | "onDragStart"
  | "onDragEnd"
  | "onAnimationStart"
  | "onAnimationEnd"
  | "onAnimationIteration"
>;

interface ButtonProps extends ButtonDomProps {
  variant?: "primary" | "secondary" | "danger" | "success" | "ghost";
  size?: "sm" | "md" | "lg";
  loading?: boolean;
  icon?: React.ReactNode;
}

export default function Button({
  variant = "primary",
  size = "md",
  loading = false,
  icon,
  children,
  className,
  disabled,
  ...props
}: ButtonProps) {
  const variants = {
    primary: "bg-accent-primary hover:bg-accent-primary/85 text-white",
    secondary:
      "bg-bg-secondary hover:bg-bg-tertiary text-text-primary border border-border",
    danger: "bg-accent-danger hover:bg-accent-danger/85 text-white",
    success: "bg-accent-success hover:bg-accent-success/85 text-white",
    ghost: "hover:bg-bg-tertiary text-text-secondary",
  };

  const sizes = {
    sm: "px-3 py-1.5 text-xs gap-1.5",
    md: "px-4 py-2 text-sm gap-2",
    lg: "px-6 py-2.5 text-base gap-2.5",
  };

  return (
    <motion.button
      className={cn(
        "inline-flex items-center justify-center font-medium rounded-[var(--radius-md)] transition-[background-color,color,transform] duration-[var(--transition-fast)] disabled:opacity-50 disabled:pointer-events-none active:translate-y-[1px]",
        variants[variant],
        sizes[size],
        className
      )}
      disabled={disabled || loading}
      whileTap={{ scale: 0.98 }}
      {...props}
    >
      {loading ? (
        <SpinnerGap size={16} weight="bold" className="animate-spin" />
      ) : (
        icon
      )}
      {children}
    </motion.button>
  );
}
