import { cn } from "../../lib/utils";

export function ToggleChip({
  active,
  label,
  onClick,
}: {
  active: boolean;
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "border-2 px-3 py-2 text-[11px] font-semibold uppercase tracking-[0.18em] transition-colors duration-[var(--transition-fast)]",
        active
          ? "border-[var(--color-text-primary)] bg-accent-primary text-white"
          : "border-[var(--color-text-primary)] bg-[var(--color-bg-secondary)] text-text-secondary hover:bg-[var(--color-bg-tertiary)] hover:text-text-primary"
      )}
    >
      {label}
    </button>
  );
}
