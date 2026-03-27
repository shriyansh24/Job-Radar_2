import { useDraggable } from "@dnd-kit/core";
import { ArrowRight, Buildings } from "@phosphor-icons/react";
import { formatDistanceToNow } from "date-fns";
import type { Application } from "../../api/pipeline";
import Badge from "../ui/Badge";
import Button from "../ui/Button";
import { Surface } from "../system/Surface";
import { cn } from "../../lib/utils";

export function PipelineStageCard({
  application,
  selected,
  onSelect,
  onAdvance,
  isAdvancing,
  canAdvance,
}: {
  application: Application;
  selected: boolean;
  onSelect: () => void;
  onAdvance: () => void;
  isAdvancing: boolean;
  canAdvance: boolean;
}) {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: application.id,
  });
  const style = transform
    ? { transform: `translate(${transform.x}px, ${transform.y}px)` }
    : undefined;

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={cn("touch-none transition-opacity duration-150", isDragging && "opacity-40")}
      {...attributes}
      {...listeners}
    >
      <Surface
        tone="subtle"
        padding="md"
        interactive
        role="button"
        tabIndex={0}
        onClick={onSelect}
        onKeyDown={(event) => {
          if (event.key === "Enter") {
            event.preventDefault();
            onSelect();
          }
        }}
        className={cn(
          "transition-transform duration-150 hover:-translate-y-1 hover:-translate-x-1",
          selected && "border-[var(--color-accent-primary)] bg-[var(--color-accent-primary-subtle)]"
        )}
      >
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-text-muted">
              {application.status}
            </div>
            <h3 className="mt-2 truncate font-display text-lg font-black uppercase tracking-[-0.05em] text-foreground">
              {application.position_title ?? "Untitled application"}
            </h3>
            <div className="mt-2 flex items-center gap-1.5 text-xs text-muted-foreground">
              <Buildings size={12} weight="bold" />
              <span className="truncate">{application.company_name ?? "Unknown company"}</span>
            </div>
          </div>
          <div className="flex shrink-0 flex-col items-end gap-2">
            <Badge variant="outline">{application.status}</Badge>
            {application.updated_at ? (
              <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-text-muted">
                {formatDistanceToNow(new Date(application.updated_at), { addSuffix: true })}
              </span>
            ) : null}
          </div>
        </div>

        <div className="mt-4 flex items-center justify-between gap-3">
          <span className="text-xs text-text-muted">{application.source ?? "Unknown source"}</span>
          {canAdvance ? (
            <Button
              variant="secondary"
              size="sm"
              onClick={(event) => {
                event.stopPropagation();
                onAdvance();
              }}
              loading={isAdvancing}
              icon={<ArrowRight size={14} weight="bold" />}
            >
              Advance
            </Button>
          ) : (
            <Badge variant="success">Final</Badge>
          )}
        </div>
      </Surface>
    </div>
  );
}
