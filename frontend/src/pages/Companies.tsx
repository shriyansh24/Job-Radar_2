import { Buildings } from "@phosphor-icons/react";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { companiesApi, type Company } from "../api/phase7a";

const stateColors: Record<string, string> = {
  verified: "bg-green-500/10 text-green-400",
  unverified: "bg-yellow-500/10 text-yellow-400",
  invalid: "bg-red-500/10 text-red-400",
};

export default function Companies() {
  const [filter, setFilter] = useState<string>("");

  const { data: companies = [], isLoading } = useQuery({
    queryKey: ["companies"],
    queryFn: () => companiesApi.list(),
  });

  const filtered = filter
    ? companies.filter((c) => c.validation_state === filter)
    : companies;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-text-primary flex items-center gap-2">
          <Buildings size={24} weight="bold" />
          Companies
        </h1>
        <div className="flex gap-2">
          {["", "verified", "unverified", "invalid"].map((state) => (
            <button
              key={state}
              onClick={() => setFilter(state)}
              className={`px-3 py-1.5 rounded-[var(--radius-md)] text-sm transition-colors ${
                filter === state
                  ? "bg-accent-primary text-white"
                  : "bg-bg-tertiary text-text-secondary hover:text-text-primary"
              }`}
            >
              {state || "All"}
            </button>
          ))}
        </div>
      </div>

      {isLoading ? (
        <div className="text-text-muted text-sm">Loading companies...</div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-12 text-text-muted">
          <Buildings size={48} className="mx-auto mb-3 opacity-50" />
          <p>No companies found</p>
        </div>
      ) : (
        <div className="border border-border rounded-[var(--radius-lg)] overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-bg-tertiary text-text-secondary">
              <tr>
                <th className="text-left px-4 py-3 font-medium">Company</th>
                <th className="text-left px-4 py-3 font-medium">Domain</th>
                <th className="text-left px-4 py-3 font-medium">ATS</th>
                <th className="text-left px-4 py-3 font-medium">Status</th>
                <th className="text-right px-4 py-3 font-medium">Jobs</th>
                <th className="text-right px-4 py-3 font-medium">Confidence</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {filtered.map((c: Company) => (
                <tr key={c.id} className="hover:bg-bg-tertiary/50 transition-colors">
                  <td className="px-4 py-3 text-text-primary font-medium">
                    {c.canonical_name}
                  </td>
                  <td className="px-4 py-3 text-text-secondary">{c.domain || "-"}</td>
                  <td className="px-4 py-3 text-text-secondary">{c.ats_provider || "-"}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-flex px-2 py-0.5 rounded text-xs font-medium ${
                        stateColors[c.validation_state] || "bg-bg-tertiary text-text-muted"
                      }`}
                    >
                      {c.validation_state}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right text-text-secondary">{c.job_count}</td>
                  <td className="px-4 py-3 text-right text-text-secondary">
                    {(c.confidence_score * 100).toFixed(0)}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
