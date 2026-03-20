import { MagnifyingGlassPlus } from "@phosphor-icons/react";
import { useQuery } from "@tanstack/react-query";
import { searchExpansionApi, type QueryTemplate } from "../api/phase7a";

export default function SearchExpansion() {
  const { data: templates = [], isLoading } = useQuery({
    queryKey: ["search-expansion", "templates"],
    queryFn: searchExpansionApi.listTemplates,
  });

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold text-text-primary flex items-center gap-2">
        <MagnifyingGlassPlus size={24} weight="bold" />
        Search Expansion
      </h1>

      <p className="text-sm text-text-secondary">
        Expand your job search queries with synonyms and related terms to find more relevant listings.
      </p>

      {isLoading ? (
        <div className="text-text-muted text-sm">Loading templates...</div>
      ) : templates.length === 0 ? (
        <div className="text-center py-12 text-text-muted">
          <MagnifyingGlassPlus size={48} className="mx-auto mb-3 opacity-50" />
          <p>No search templates yet</p>
          <p className="text-xs mt-1">Templates will appear here as you configure search expansion rules.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {templates.map((t: QueryTemplate) => (
            <div
              key={t.id}
              className="border border-border rounded-[var(--radius-lg)] p-4 bg-bg-secondary"
            >
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-medium text-text-primary">{t.name}</h3>
                <div className="flex items-center gap-2">
                  <span
                    className={`px-2 py-0.5 rounded text-xs ${
                      t.strictness === "strict"
                        ? "bg-red-500/10 text-red-400"
                        : t.strictness === "loose"
                          ? "bg-green-500/10 text-green-400"
                          : "bg-blue-500/10 text-blue-400"
                    }`}
                  >
                    {t.strictness}
                  </span>
                  <span
                    className={`w-2 h-2 rounded-full ${
                      t.is_active ? "bg-green-500" : "bg-gray-500"
                    }`}
                    title={t.is_active ? "Active" : "Inactive"}
                  />
                </div>
              </div>

              <p className="text-sm text-text-secondary font-mono bg-bg-tertiary px-3 py-2 rounded-[var(--radius-md)]">
                {t.base_query}
              </p>

              {t.expanded_queries && t.expanded_queries.length > 0 && (
                <div className="mt-3">
                  <p className="text-xs text-text-muted mb-1">Expanded queries:</p>
                  <div className="flex flex-wrap gap-1.5">
                    {t.expanded_queries.map((q, i) => (
                      <span
                        key={i}
                        className="px-2 py-0.5 rounded-full text-xs bg-bg-tertiary text-text-secondary"
                      >
                        {q}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
