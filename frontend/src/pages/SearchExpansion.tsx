import { Lightning, MagnifyingGlassPlus, Sparkle, TerminalWindow } from "@phosphor-icons/react";
import { useMutation } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { searchExpansionApi } from "../api/phase7a";
import { MetricStrip } from "../components/system/MetricStrip";
import { PageHeader } from "../components/system/PageHeader";
import { SectionHeader } from "../components/system/SectionHeader";
import { SplitWorkspace } from "../components/system/SplitWorkspace";
import { StateBlock } from "../components/system/StateBlock";
import { Surface } from "../components/system/Surface";
import Badge from "../components/ui/Badge";
import Button from "../components/ui/Button";
import EmptyState from "../components/ui/EmptyState";
import Input from "../components/ui/Input";
import Skeleton from "../components/ui/Skeleton";
import { toast } from "../components/ui/toastService";

const SUGGESTED_QUERIES = [
  "senior frontend engineer",
  "product designer fintech",
  "ai product manager remote",
  "staff software engineer platform",
] as const;

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
      className="hard-press border-2 border-border bg-card px-3 py-2 font-mono text-[11px] font-bold uppercase tracking-[0.16em] text-text-secondary shadow-[var(--shadow-xs)] hover:text-text-primary"
    >
      {value}
    </button>
  );
}

export default function SearchExpansion() {
  const [query, setQuery] = useState("");
  const [history, setHistory] = useState<string[]>([]);

  const expandMutation = useMutation({
    mutationFn: (rawQuery: string) => searchExpansionApi.expand(rawQuery),
    onSuccess: (result, rawQuery) => {
      setHistory((current) => [rawQuery, ...current.filter((entry) => entry !== rawQuery)].slice(0, 6));
      toast("success", "Query expansion complete");
      if (!result.expanded_terms.length && !result.synonyms.length) {
        toast("info", "Expansion returned no additional terms yet");
      }
    },
    onError: () => toast("error", "Search expansion failed"),
  });

  const latest = expandMutation.data ?? null;

  const metrics = useMemo(
    () => [
      {
        key: "history",
        label: "Recent runs",
        value: history.length.toLocaleString(),
        hint: "Queries expanded in this session.",
        icon: <TerminalWindow size={18} weight="bold" />,
      },
      {
        key: "expanded",
        label: "Expanded terms",
        value: `${latest?.expanded_terms.length ?? 0}`,
        hint: "Additional role variants generated from the latest run.",
        icon: <Sparkle size={18} weight="fill" />,
        tone: latest?.expanded_terms.length ? ("success" as const) : ("default" as const),
      },
      {
        key: "synonyms",
        label: "Synonyms",
        value: `${latest?.synonyms.length ?? 0}`,
        hint: "Parallel phrases surfaced for the active query.",
        icon: <MagnifyingGlassPlus size={18} weight="bold" />,
      },
      {
        key: "status",
        label: "Engine state",
        value: expandMutation.isPending ? "Running" : latest ? "Complete" : "Idle",
        hint: "Current search-expansion pipeline state.",
        icon: <Lightning size={18} weight="bold" />,
        tone: expandMutation.isPending ? ("warning" as const) : ("default" as const),
      },
    ],
    [expandMutation.isPending, history.length, latest]
  );

  const runExpansion = (value = query) => {
    const normalized = value.trim();
    if (!normalized) return;
    setQuery(normalized);
    expandMutation.mutate(normalized);
  };

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Operations"
        title="Search Expansion"
        description="Run the live backend expansion endpoint against a role query, inspect the returned synonyms and related terms, and keep a short operational history without inventing a stale template system."
        actions={
          <Button
            variant="primary"
            size="sm"
            onClick={() => runExpansion()}
            loading={expandMutation.isPending}
            icon={<Sparkle size={14} weight="fill" />}
          >
            Expand query
          </Button>
        }
        meta={
          <div className="flex flex-wrap gap-2">
            <Badge variant="info" size="sm">
              Live backend contract
            </Badge>
            <Badge variant={latest ? "success" : "default"} size="sm">
              {latest ? "Result loaded" : "Awaiting query"}
            </Badge>
          </div>
        }
      />

      <MetricStrip items={metrics} />

      <SplitWorkspace
        primary={
          <div className="space-y-6">
            <Surface tone="default" padding="lg" radius="xl">
              <SectionHeader
                title="Expansion console"
                description="Use the same endpoint the backend exposes today. This view is intentionally concrete: one input, one response, no fake template inventory."
              />
              <div className="mt-6 grid gap-4 lg:grid-cols-[minmax(0,1fr)_200px]">
                <Input
                  label="Base query"
                  placeholder="senior frontend engineer"
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  icon={<MagnifyingGlassPlus size={16} weight="bold" />}
                  onKeyDown={(event) => {
                    if (event.key === "Enter") {
                      event.preventDefault();
                      runExpansion();
                    }
                  }}
                />
                <div className="flex items-end">
                  <Button
                    className="w-full"
                    loading={expandMutation.isPending}
                    disabled={!query.trim()}
                    onClick={() => runExpansion()}
                    icon={<Sparkle size={14} weight="fill" />}
                  >
                    Expand query
                  </Button>
                </div>
              </div>

              <div className="mt-5 flex flex-wrap gap-2 border-t-2 border-border pt-5">
                {SUGGESTED_QUERIES.map((entry) => (
                  <QueryChip key={entry} value={entry} onClick={runExpansion} />
                ))}
              </div>
            </Surface>

            {expandMutation.isPending ? (
              <Surface tone="default" padding="lg" radius="xl">
                <Skeleton variant="text" className="h-5 w-48" />
                <Skeleton variant="rect" className="mt-6 h-24 w-full" />
                <div className="mt-4 flex flex-wrap gap-2">
                  <Skeleton variant="rect" className="h-10 w-32" />
                  <Skeleton variant="rect" className="h-10 w-28" />
                  <Skeleton variant="rect" className="h-10 w-36" />
                </div>
              </Surface>
            ) : latest ? (
              <Surface tone="default" padding="lg" radius="xl">
                <SectionHeader
                  title="Expansion result"
                  description={latest.message || "Expanded search result returned from the backend."}
                />

                <div className="mt-6 grid gap-4 xl:grid-cols-3">
                  <div className="border-2 border-border bg-[var(--color-bg-tertiary)] p-4 shadow-[var(--shadow-xs)] xl:col-span-3">
                    <div className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
                      Original query
                    </div>
                    <div className="mt-3 text-2xl font-black uppercase tracking-[-0.05em] text-text-primary">
                      {latest.original_query}
                    </div>
                  </div>

                  <div className="xl:col-span-2">
                    <div className="border-2 border-border bg-card p-4 shadow-[var(--shadow-xs)]">
                      <div className="flex items-center gap-2">
                        <Sparkle size={16} weight="fill" className="text-accent-primary" />
                        <div className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
                          Expanded terms
                        </div>
                      </div>
                      {latest.expanded_terms.length ? (
                        <div className="mt-4 flex flex-wrap gap-2">
                          {latest.expanded_terms.map((term) => (
                            <Badge key={term} variant="info" size="md">
                              {term}
                            </Badge>
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
                    <div className="border-2 border-border bg-card p-4 shadow-[var(--shadow-xs)]">
                      <div className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
                        Synonyms
                      </div>
                      {latest.synonyms.length ? (
                        <div className="mt-4 space-y-2">
                          {latest.synonyms.map((term) => (
                            <div
                              key={term}
                              className="border-2 border-border bg-[var(--color-bg-tertiary)] px-3 py-2 font-mono text-[11px] font-bold uppercase tracking-[0.16em] text-text-secondary"
                            >
                              {term}
                            </div>
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
            ) : (
              <Surface tone="default" padding="lg" radius="xl">
                <EmptyState
                  icon={<MagnifyingGlassPlus size={40} weight="bold" />}
                  title="No expansion run yet"
                  description="Enter a base role query or use one of the suggested examples to hit the live backend endpoint."
                />
              </Surface>
            )}
          </div>
        }
        secondary={
          <div className="space-y-4">
            <StateBlock
              tone="neutral"
              icon={<TerminalWindow size={18} weight="bold" />}
              title="Current backend reality"
              description="The service currently returns a direct expansion response, not a stored template registry. This page now reflects that contract instead of pretending a template list exists."
            />
            <StateBlock
              tone="warning"
              icon={<Lightning size={18} weight="bold" />}
              title="Operational note"
              description="If the backend has not been upgraded with LLM expansion yet, you may see empty synonym and expansion arrays with a status message explaining the current state."
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
                      onClick={() => runExpansion(entry)}
                      className="hard-press flex w-full items-center justify-between border-2 border-border bg-[var(--color-bg-tertiary)] px-3 py-3 text-left shadow-[var(--shadow-xs)]"
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
        }
      />
    </div>
  );
}
