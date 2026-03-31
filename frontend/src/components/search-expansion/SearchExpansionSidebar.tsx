import { Lightning, Sparkle, TerminalWindow } from "@phosphor-icons/react";
import { StateBlock } from "../system/StateBlock";
import { Surface } from "../system/Surface";

export function SearchExpansionSidebar({
  history,
  onRun,
}: {
  history: string[];
  onRun: (value?: string) => void;
}) {
  return (
    <div className="space-y-4">
      <StateBlock
        tone="neutral"
        icon={<TerminalWindow size={18} weight="bold" />}
        title="Semantic handoff"
        description="Use any returned term to jump straight into semantic search on the jobs route."
      />
      <StateBlock
        tone="warning"
        icon={<Lightning size={18} weight="bold" />}
        title="Engine note"
        description="If the backend returns empty arrays, the endpoint is reachable but there are no extra terms for that query yet."
      />
      {history.length ? (
        <Surface tone="default" padding="md" radius="xl">
          <div className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
            Recent queries
          </div>
          <div className="mt-4 space-y-2">
            {history.map((entry) => (
              <button
                key={entry}
                type="button"
                onClick={() => onRun(entry)}
                className="hard-press flex w-full items-center justify-between border-2 border-border bg-[var(--color-bg-tertiary)] px-3 py-3 text-left"
              >
                <span className="font-mono text-[11px] font-bold uppercase tracking-[0.16em] text-text-primary">
                  {entry}
                </span>
                <Sparkle size={14} weight="fill" className="text-accent-primary" />
              </button>
            ))}
          </div>
        </Surface>
      ) : null}
    </div>
  );
}
