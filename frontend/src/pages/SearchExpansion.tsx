import {
  Lightning,
  MagnifyingGlassPlus,
  Sparkle,
  TerminalWindow,
} from "@phosphor-icons/react";
import { useMutation } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { searchExpansionApi } from "../api/phase7a";
import { SearchExpansionConsole } from "../components/search-expansion/SearchExpansionConsole";
import { SearchExpansionResultPanel } from "../components/search-expansion/SearchExpansionResultPanel";
import { SearchExpansionSidebar } from "../components/search-expansion/SearchExpansionSidebar";
import { MetricStrip } from "../components/system/MetricStrip";
import { PageHeader } from "../components/system/PageHeader";
import { SplitWorkspace } from "../components/system/SplitWorkspace";
import Badge from "../components/ui/Badge";
import Button from "../components/ui/Button";
import { toast } from "../components/ui/toastService";

const SUGGESTED_QUERIES = [
  "senior frontend engineer",
  "product designer fintech",
  "ai product manager remote",
  "staff software engineer platform",
] as const;

export default function SearchExpansion() {
  const navigate = useNavigate();
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

  const openSemanticSearch = (value: string) => {
    const normalized = value.trim();
    if (!normalized) return;
    navigate(`/jobs?mode=semantic&q=${encodeURIComponent(normalized)}`);
  };

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
        hint: "Terms returned from the latest run.",
        icon: <Sparkle size={18} weight="fill" />,
        tone: latest?.expanded_terms.length ? ("success" as const) : ("default" as const),
      },
      {
        key: "synonyms",
        label: "Synonyms",
        value: `${latest?.synonyms.length ?? 0}`,
        hint: "Alternate phrases returned.",
        icon: <MagnifyingGlassPlus size={18} weight="bold" />,
      },
      {
        key: "status",
        label: "Engine state",
        value: expandMutation.isPending ? "Running" : latest ? "Complete" : "Idle",
        hint: "Current endpoint state.",
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
        description="Run the live expansion endpoint, review the response, and send a term into semantic search."
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
              Live endpoint
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
            <SearchExpansionConsole
              query={query}
              isPending={expandMutation.isPending}
              suggestedQueries={SUGGESTED_QUERIES}
              onQueryChange={setQuery}
              onRun={runExpansion}
            />

            <SearchExpansionResultPanel
              latest={latest}
              isPending={expandMutation.isPending}
              onOpenSemanticSearch={openSemanticSearch}
            />
          </div>
        }
        secondary={<SearchExpansionSidebar history={history} onRun={runExpansion} />}
      />
    </div>
  );
}
