import { Briefcase, Clock, Cloud, Database } from "@phosphor-icons/react";
import { SectionHeader } from "../system/SectionHeader";
import { Surface } from "../system/Surface";
import { AdminDiagnosticCard } from "./AdminDiagnosticCard";

export function AdminDiagnosticsPanel({
  loading,
  pythonVersion,
  platform,
  applicationCount,
  totalJobs,
}: {
  loading: boolean;
  pythonVersion: string;
  platform: string;
  applicationCount: string | number;
  totalJobs: string | number;
}) {
  return (
    <Surface className="border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-secondary)]">
      <SectionHeader title="Diagnostics" description="Operational counters and environment details surfaced by the backend." />
      <div className="mt-6 grid gap-3 sm:grid-cols-2">
        <AdminDiagnosticCard icon={<Cloud size={16} weight="bold" />} label="Python version" value={pythonVersion} loading={loading} />
        <AdminDiagnosticCard icon={<Database size={16} />} label="Platform" value={platform} loading={loading} />
        <AdminDiagnosticCard icon={<Clock size={16} />} label="Applications" value={applicationCount} loading={loading} />
        <AdminDiagnosticCard
          icon={<Briefcase size={16} weight="bold" />}
          label="Total jobs"
          value={typeof totalJobs === "number" ? totalJobs.toLocaleString() : totalJobs}
          loading={loading}
        />
      </div>
    </Surface>
  );
}
