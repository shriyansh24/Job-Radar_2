import {
  ArrowSquareOut,
  MagnifyingGlassPlus,
  Sparkle,
} from "@phosphor-icons/react";
import type { SearchExpansionResult } from "../../api/phase7a";
import { SectionHeader } from "../system/SectionHeader";
import { Surface } from "../system/Surface";
import Button from "../ui/Button";
import EmptyState from "../ui/EmptyState";
import Skeleton from "../ui/Skeleton";

export function SearchExpansionResultPanel({
  latest,
  isPending,
  onOpenSemanticSearch,
}: {
  latest: SearchExpansionResult | null;
  isPending: boolean;
  onOpenSemanticSearch: (value: string) => void;
}) {
  if (isPending) {
    return (
      <Surface tone="default" padding="lg" radius="xl">
        <Skeleton variant="text" className="h-5 w-48" />
        <Skeleton variant="rect" className="mt-6 h-24 w-full" />
        <div className="mt-4 flex flex-wrap gap-2">
          <Skeleton variant="rect" className="h-10 w-32" />
          <Skeleton variant="rect" className="h-10 w-28" />
          <Skeleton variant="rect" className="h-10 w-36" />
        </div>
      </Surface>
    );
  }

  if (!latest) {
    return (
      <Surface tone="default" padding="lg" radius="xl">
        <EmptyState
          icon={<MagnifyingGlassPlus size={40} weight="bold" />}
          title="No expansion run yet"
          description="Enter a base role query or use one of the suggested examples to hit the live backend endpoint."
        />
      </Surface>
    );
  }

  return (
    <Surface tone="default" padding="lg" radius="xl">
      <SectionHeader
        title="Expansion result"
        description={latest.message || "Latest response returned from the backend."}
      />

      <div className="mt-6 grid gap-4 xl:grid-cols-3">
        <div className="border-2 border-border bg-[var(--color-bg-secondary)] p-4 shadow-[var(--shadow-xs)] xl:col-span-3">
          <div className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
            Original query
          </div>
          <div className="mt-3 text-2xl font-black uppercase tracking-[-0.05em] text-text-primary">
            {latest.original_query}
          </div>
          <div className="mt-4">
            <Button
              variant="secondary"
              size="sm"
              onClick={() => onOpenSemanticSearch(latest.original_query)}
              icon={<ArrowSquareOut size={14} weight="bold" />}
            >
              Open in jobs
            </Button>
          </div>
        </div>

        <div className="xl:col-span-2">
          <div className="border-2 border-border bg-[var(--color-bg-secondary)] p-4 shadow-[var(--shadow-xs)]">
            <div className="flex items-center gap-2">
              <Sparkle size={16} weight="fill" className="text-accent-primary" />
              <div className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
                Expanded terms
              </div>
            </div>
            {latest.expanded_terms.length ? (
              <div className="mt-4 flex flex-wrap gap-2">
                {latest.expanded_terms.map((term) => (
                  <Button
                    key={term}
                    variant="secondary"
                    size="sm"
                    onClick={() => onOpenSemanticSearch(term)}
                    icon={<ArrowSquareOut size={14} weight="bold" />}
                  >
                    {term}
                  </Button>
                ))}
              </div>
            ) : (
              <p className="mt-4 text-sm leading-6 text-text-secondary">
                No expanded terms were returned for this query.
              </p>
            )}
          </div>
        </div>

        <div>
          <div className="border-2 border-border bg-[var(--color-bg-secondary)] p-4 shadow-[var(--shadow-xs)]">
            <div className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
              Synonyms
            </div>
            {latest.synonyms.length ? (
              <div className="mt-4 space-y-2">
                {latest.synonyms.map((term) => (
                  <button
                    key={term}
                    type="button"
                    onClick={() => onOpenSemanticSearch(term)}
                    className="border-2 border-border bg-[var(--color-bg-tertiary)] px-3 py-2 font-mono text-[11px] font-bold uppercase tracking-[0.16em] text-text-secondary"
                  >
                    {term}
                  </button>
                ))}
              </div>
            ) : (
              <p className="mt-4 text-sm leading-6 text-text-secondary">
                No synonyms were returned.
              </p>
            )}
          </div>
        </div>
      </div>
    </Surface>
  );
}
