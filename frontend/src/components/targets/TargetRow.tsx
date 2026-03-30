import { type ScrapeTarget } from "../../api/scraper";
import Badge from "../ui/Badge";
import Toggle from "../ui/Toggle";
import { cn } from "../../lib/utils";
import { atsVariant, priorityVariant, relativeTime } from "./targetUtils";

export function TargetRow({
  target,
  isSelected,
  onClick,
  onToggleEnabled,
}: {
  target: ScrapeTarget;
  isSelected: boolean;
  onClick: () => void;
  onToggleEnabled: (enabled: boolean) => void;
}) {
  const rowBg = target.quarantined
    ? "bg-accent-danger/5 hover:bg-accent-danger/10 border-l-4 border-l-accent-danger"
    : isSelected
      ? "bg-bg-tertiary"
      : "hover:bg-bg-tertiary/60";

  return (
    <div
      role="button"
      tabIndex={0}
      className={cn(
        "grid cursor-pointer gap-3 border-b-2 border-border px-5 py-4 transition-colors md:grid-cols-[minmax(0,1.5fr)_140px_140px_150px] md:items-start",
        rowBg
      )}
      onClick={onClick}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          onClick();
        }
      }}
    >
      <div className="min-w-0">
        <p className="truncate text-lg font-black uppercase tracking-[-0.05em] text-text-primary">
          {target.company_name ?? "-"}
        </p>
        <p className="mt-2 truncate text-sm text-text-muted">{target.url}</p>
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <Badge variant={priorityVariant(target.priority_class)} size="sm">
            {target.priority_class}
          </Badge>
          <Badge variant={atsVariant(target.ats_vendor)} size="sm">
            {target.ats_vendor ?? "unknown"}
          </Badge>
          {target.quarantined ? (
            <Badge variant="danger" size="sm">
              quarantined
            </Badge>
          ) : null}
          {target.consecutive_failures > 0 ? (
            <span className="font-mono text-xs text-accent-danger">
              {target.consecutive_failures}x fail
            </span>
          ) : null}
        </div>
      </div>
      <div>
        <p className="font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-text-muted md:hidden">
          Source Kind
        </p>
        <p className="text-sm text-text-secondary">Source: {target.source_kind}</p>
      </div>
      <div>
        <p className="font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-text-muted md:hidden">
          Last Success
        </p>
        <p className="text-sm text-text-secondary">{relativeTime(target.last_success_at)}</p>
      </div>
      <div className="flex items-center justify-between gap-3 md:justify-end">
        <p className="font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-text-muted md:hidden">
          Enabled
        </p>
        <div onClick={(event) => event.stopPropagation()}>
          <Toggle checked={target.enabled} onChange={onToggleEnabled} />
        </div>
      </div>
    </div>
  );
}
