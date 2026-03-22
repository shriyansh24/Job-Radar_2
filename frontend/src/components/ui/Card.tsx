import { cn } from "../../lib/utils";

interface CardProps {
  children: React.ReactNode;
  className?: string;
  hover?: boolean;
  onClick?: () => void;
  padding?: "none" | "sm" | "md" | "lg";
}

export default function Card({
  children,
  className,
  hover,
  onClick,
  padding = "md",
}: CardProps) {
  const paddings = {
    none: "",
    sm: "p-4",
    md: "p-6",
    lg: "p-8",
  };

  return (
    <div
      className={cn(
        "bg-bg-secondary border border-border rounded-[var(--radius-xl)] shadow-[var(--shadow-xs)] transition-[transform,box-shadow,border-color] duration-[var(--transition-normal)]",
        hover &&
          "hover:shadow-[var(--shadow-card-hover)] hover:-translate-y-[2px] hover:border-border-hover cursor-pointer",
        paddings[padding],
        className
      )}
      onClick={onClick}
    >
      {children}
    </div>
  );
}
