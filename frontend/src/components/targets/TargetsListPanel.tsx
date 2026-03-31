import { CaretLeft, CaretRight, Crosshair } from "@phosphor-icons/react";
import type { ScrapeTarget } from "../../api/scraper";
import EmptyState from "../ui/EmptyState";
import Button from "../ui/Button";
import { Surface } from "../system/Surface";
import { TargetRow } from "./TargetRow";
import { TargetRowSkeleton } from "./TargetRowSkeleton";

export function TargetsListPanel({
  targets,
  totalCount,
  page,
  isLoading,
  isError,
  hasMore,
  selectedId,
  onCreateCareerPage,
  onSelectTarget,
  onToggleEnabled,
  onPreviousPage,
  onNextPage,
}: {
  targets: ScrapeTarget[];
  totalCount: number;
  page: number;
  isLoading: boolean;
  isError: boolean;
  hasMore: boolean;
  selectedId: string | null;
  onCreateCareerPage: () => void;
  onSelectTarget: (id: string) => void;
  onToggleEnabled: (id: string, enabled: boolean) => void;
  onPreviousPage: () => void;
  onNextPage: () => void;
}) {
  return (
    <Surface tone="default" padding="none" radius="xl" className="brutal-panel overflow-hidden">
      <div className="border-b-2 border-border px-5 py-4">
        <div className="flex items-baseline justify-between gap-3">
          <div>
            <div className="text-sm font-black uppercase tracking-[-0.03em] text-text-primary">
              Targets
            </div>
            <div className="mt-1 text-sm text-muted-foreground">
              <span className="font-mono text-text-secondary">{targets.length}</span> of {totalCount} shown
            </div>
          </div>
          <div className="font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
            Page {page + 1}
          </div>
        </div>
      </div>

      <div className="min-h-[420px]">
        {isError ? (
          <div className="p-8 text-center text-sm text-accent-danger">
            Failed to load targets. Please try again.
          </div>
        ) : isLoading ? (
          Array.from({ length: 10 }).map((_, index) => <TargetRowSkeleton key={index} />)
        ) : targets.length === 0 ? (
          <div className="p-6">
            <EmptyState
              icon={<Crosshair size={40} weight="bold" />}
              title="No targets found"
              description="Import targets or adjust your filters"
              action={{ label: "Add Career Page", onClick: onCreateCareerPage }}
            />
          </div>
        ) : (
          targets.map((target) => (
            <TargetRow
              key={target.id}
              target={target}
              isSelected={target.id === selectedId}
              onClick={() => onSelectTarget(target.id)}
              onToggleEnabled={(enabled) => onToggleEnabled(target.id, enabled)}
            />
          ))
        )}
      </div>

      <div className="flex items-center justify-between border-t-2 border-border px-5 py-3">
        <span className="text-xs text-text-muted">
          Page <span className="font-mono text-text-secondary">{page + 1}</span>
        </span>
        <div className="flex gap-1">
          <Button
            variant="ghost"
            size="sm"
            disabled={page === 0}
            onClick={onPreviousPage}
            icon={<CaretLeft size={14} weight="bold" />}
          >
            Prev
          </Button>
          <Button
            variant="ghost"
            size="sm"
            disabled={!hasMore}
            onClick={onNextPage}
            icon={<CaretRight size={14} weight="bold" />}
          >
            Next
          </Button>
        </div>
      </div>
    </Surface>
  );
}
