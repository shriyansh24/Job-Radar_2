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
        "bg-bg-secondary border border-border rounded-[var(--radius-xl)] shadow-[var(--shadow-sm)]",
        hover &&
          "hover:shadow-[var(--shadow-md)] hover:-translate-y-[1px] transition-[transform,box-shadow] duration-[var(--transition-fast)] cursor-pointer",
        paddings[padding],
        className
      )}
      onClick={onClick}
    >
      {children}
    </div>
  );
}
