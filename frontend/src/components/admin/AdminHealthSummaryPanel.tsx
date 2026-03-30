import Badge from "../ui/Badge";
import Skeleton from "../ui/Skeleton";
import { SectionHeader } from "../system/SectionHeader";
import { Surface } from "../system/Surface";

export function AdminHealthSummaryPanel({
  loading,
  apiStatus,
  dbOnline,
  healthySources,
  sourceCount,
}: {
  loading: boolean;
  apiStatus: string;
  dbOnline: boolean;
  healthySources: number;
  sourceCount: number;
}) {
  return (
    <Surface className="border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-secondary)]">
      <SectionHeader title="System health" description="Live service connectivity and environment status." />
      {loading ? (
        <div className="mt-6 grid gap-3 sm:grid-cols-3">
          {Array.from({ length: 3 }).map((_, index) => (
            <div key={index} className="border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-secondary)] px-4 py-4">
              <Skeleton variant="text" className="h-4 w-20" />
              <Skeleton variant="text" className="mt-4 h-6 w-24" />
            </div>
          ))}
        </div>
      ) : (
        <>
          <div className="mt-6 grid gap-3 sm:grid-cols-3">
            <div className="border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-secondary)] px-4 py-4">
              <p className="font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-text-muted">Database</p>
              <div className="mt-4">
                <Badge variant={dbOnline ? "success" : "danger"}>{dbOnline ? "Online" : "Offline"}</Badge>
              </div>
            </div>
            <div className="border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-secondary)] px-4 py-4">
              <p className="font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-text-muted">Redis</p>
              <div className="mt-4">
                <Badge variant="success">Connected</Badge>
              </div>
            </div>
            <div className="border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-secondary)] px-4 py-4">
              <p className="font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-text-muted">API status</p>
              <div className="mt-4">
                <Badge variant={apiStatus === "ok" ? "success" : "danger"}>{apiStatus}</Badge>
              </div>
            </div>
          </div>
          <div className="mt-4 text-[11px] font-bold uppercase tracking-[0.18em] text-text-muted">
            {healthySources}/{sourceCount} healthy
          </div>
        </>
      )}
    </Surface>
  );
}
