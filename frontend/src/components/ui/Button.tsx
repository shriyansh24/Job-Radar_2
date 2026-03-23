import type React from "react";
import { SpinnerGap } from "@phosphor-icons/react";
import { motion } from "framer-motion";
import type { VariantProps } from "class-variance-authority";
import { cn } from "../../lib/utils";
import { buttonVariants } from "./buttonVariants";

type ButtonDomProps = Omit<
  React.ButtonHTMLAttributes<HTMLButtonElement>,
  | "onDrag"
  | "onDragStart"
  | "onDragEnd"
  | "onAnimationStart"
  | "onAnimationEnd"
  | "onAnimationIteration"
>;

export interface ButtonProps
  extends ButtonDomProps,
    VariantProps<typeof buttonVariants> {
  loading?: boolean;
  icon?: React.ReactNode;
}

function Button({
  variant = "primary",
  size = "md",
  loading = false,
  icon,
  children,
  className,
  disabled,
  ...props
}: ButtonProps) {
  return (
    <motion.button
      className={cn(buttonVariants({ variant, size }), className)}
      disabled={disabled || loading}
      whileTap={{ scale: 0.985 }}
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

export { Button };
export default Button;
