import { Heartbeat } from "@phosphor-icons/react";
import { useQuery } from "@tanstack/react-query";
import { sourceHealthApi, type SourceHealth } from "../api/phase7a";

const healthColors: Record<string, string> = {
  healthy: "bg-green-500",
  degraded: "bg-yellow-500",
  failing: "bg-red-500",
  unknown: "bg-gray-500",
};

const healthBadgeColors: Record<string, string> = {
  healthy: "bg-green-500/10 text-green-400",
  degraded: "bg-yellow-500/10 text-yellow-400",
  failing: "bg-red-500/10 text-red-400",
  unknown: "bg-bg-tertiary text-text-muted",
};

export default function Sources() {
  const { data: sources = [], isLoading } = useQuery({
    queryKey: ["source-health"],
    queryFn: sourceHealthApi.list,
    refetchInterval: 60_000,
  });

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold text-text-primary flex items-center gap-2">
        <Heartbeat size={24} weight="bold" />
        Source Health
      </h1>

      {isLoading ? (
        <div className="text-text-muted text-sm">Loading sources...</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {sources.map((s: SourceHealth) => (
            <div
              key={s.id}
              className="border border-border rounded-[var(--radius-lg)] p-4 bg-bg-secondary"
            >
              <div className="flex items-center justify-between mb-3">
                <span className="font-medium text-text-primary capitalize">
                  {s.source_name}
                </span>
                <span
                  className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-medium ${
                    healthBadgeColors[s.health_state] || healthBadgeColors.unknown
                  }`}
                >
                  <span
                    className={`w-2 h-2 rounded-full ${healthColors[s.health_state] || healthColors.unknown}`}
                  />
                  {s.health_state}
                </span>
              </div>

              <div className="space-y-2 text-sm">
                <div className="flex justify-between text-text-secondary">
                  <span>Jobs found</span>
                  <span className="text-text-primary font-mono">{s.total_jobs_found}</span>
                </div>
                <div className="flex justify-between text-text-secondary">
                  <span>Quality</span>
                  <span className="text-text-primary font-mono">
                    {(s.quality_score * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="flex justify-between text-text-secondary">
                  <span>Failures</span>
                  <span className="text-text-primary font-mono">{s.failure_count}</span>
                </div>
                {s.last_check_at && (
                  <div className="flex justify-between text-text-secondary">
                    <span>Last check</span>
                    <span className="text-text-muted text-xs">
                      {new Date(s.last_check_at).toLocaleString()}
                    </span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
