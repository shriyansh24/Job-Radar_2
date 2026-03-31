import { MagnifyingGlassPlus, Sparkle } from "@phosphor-icons/react";
import { SectionHeader } from "../system/SectionHeader";
import { Surface } from "../system/Surface";
import Button from "../ui/Button";
import Input from "../ui/Input";

function QueryChip({
  value,
  onClick,
}: {
  value: string;
  onClick: (value: string) => void;
}) {
  return (
    <button
      type="button"
      onClick={() => onClick(value)}
      className="hard-press border-2 border-border bg-[var(--color-bg-secondary)] px-3 py-2 font-mono text-[11px] font-bold uppercase tracking-[0.16em] text-text-secondary hover:bg-[var(--color-bg-tertiary)] hover:text-text-primary"
    >
      {value}
    </button>
  );
}

export function SearchExpansionConsole({
  query,
  isPending,
  suggestedQueries,
  onQueryChange,
  onRun,
}: {
  query: string;
  isPending: boolean;
  suggestedQueries: readonly string[];
  onQueryChange: (value: string) => void;
  onRun: (value?: string) => void;
}) {
  return (
    <Surface tone="default" padding="lg" radius="xl">
      <SectionHeader
        title="Expansion console"
        description="One query in, one response out."
      />
      <div className="mt-6 grid gap-4 lg:grid-cols-[minmax(0,1fr)_200px]">
        <Input
          label="Base query"
          placeholder="senior frontend engineer"
          value={query}
          onChange={(event) => onQueryChange(event.target.value)}
          icon={<MagnifyingGlassPlus size={16} weight="bold" />}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              event.preventDefault();
              onRun();
            }
          }}
        />
        <div className="flex items-end">
          <Button
            className="w-full"
            loading={isPending}
            disabled={!query.trim()}
            onClick={() => onRun()}
            icon={<Sparkle size={14} weight="fill" />}
          >
            Expand query
          </Button>
        </div>
      </div>

      <div className="mt-5 flex flex-wrap gap-2 border-t-2 border-border pt-5">
        {suggestedQueries.map((entry) => (
          <QueryChip key={entry} value={entry} onClick={onRun} />
        ))}
      </div>
    </Surface>
  );
}
