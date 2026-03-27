import { Buildings, Globe } from "@phosphor-icons/react";
import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { companiesApi, type Company } from "../api/phase7a";
import { MetricStrip } from "../components/system/MetricStrip";
import { PageHeader, SectionHeader, Surface } from "../components/system";
import Badge from "../components/ui/Badge";
import EmptyState from "../components/ui/EmptyState";
import Skeleton from "../components/ui/Skeleton";
import { cn } from "../lib/utils";

function companyStateVariant(state: string): "success" | "warning" | "danger" | "default" {
  switch (state) {
    case "verified":
      return "success";
    case "unverified":
      return "warning";
    case "invalid":
      return "danger";
    default:
      return "default";
  }
}

const FILTER_OPTIONS = [
  { value: "", label: "All" },
  { value: "verified", label: "verified" },
  { value: "unverified", label: "unverified" },
  { value: "invalid", label: "invalid" },
];

const CompanyMetricStrip = MetricStrip;

export default function Companies() {
  const [filter, setFilter] = useState("");

  const { data: companies = [], isLoading } = useQuery({
    queryKey: ["companies"],
    queryFn: () => companiesApi.list(),
  });

  const filtered = useMemo(
    () => (filter ? companies.filter((company) => company.validation_state === filter) : companies),
    [companies, filter]
  );

  const verifiedCount = companies.filter((company) => company.validation_state === "verified").length;
  const metricItems = [
    {
      key: "registry",
      label: "Registry Size",
      value: isLoading ? "..." : companies.length.toLocaleString(),
      hint: "Canonical company records in the active registry.",
      tone: "default" as const,
    },
    {
      key: "verified",
      label: "Verified",
      value: isLoading ? "..." : verifiedCount.toLocaleString(),
      hint: "Companies with accepted validation.",
      tone: "success" as const,
    },
    {
      key: "visible",
      label: "Visible Now",
      value: isLoading ? "..." : filtered.length.toLocaleString(),
      hint: "Rows matching the active validation filter.",
      tone: "warning" as const,
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Operations"
        title="Companies"
        description="Canonical company records, ATS fingerprints, and validation confidence for the discovery pipeline."
        actions={
          <div className="flex flex-wrap gap-2">
            {FILTER_OPTIONS.map((option) => (
              <button
                key={option.value || "all"}
                type="button"
                onClick={() => setFilter(option.value)}
                className={cn(
                  "hard-press border-2 border-border px-3 py-2 font-mono text-[10px] font-bold uppercase tracking-[0.18em] transition-[background-color,color,border-color] duration-[var(--transition-fast)]",
                  filter === option.value
                    ? "bg-accent-primary text-primary-foreground shadow-[var(--shadow-sm)]"
                    : "bg-card text-text-secondary hover:text-text-primary"
                )}
              >
                {option.label}
              </button>
            ))}
          </div>
        }
        meta={
          <>
            <span className="border-2 border-border bg-[var(--color-bg-tertiary)] px-3 py-2 font-mono font-bold uppercase tracking-[0.16em]">
              {companies.length} records
            </span>
            <span className="border-2 border-border bg-[var(--color-bg-tertiary)] px-3 py-2 font-mono font-bold uppercase tracking-[0.16em]">
              {verifiedCount} verified
            </span>
          </>
        }
      />

      <CompanyMetricStrip
        items={metricItems.map((item) => ({
          ...item,
          hint: item.hint,
        }))}
      />

      {isLoading ? (
        <Surface padding="none">
          <div className="border-b-2 border-border px-5 py-5">
            <SectionHeader
              title="Company Registry"
              description="Validation state, ATS routing, and confidence signals for each canonical company."
            />
          </div>
          <div className="divide-y-2 divide-border">
            {Array.from({ length: 5 }).map((_, index) => (
              <div
                key={index}
                className="grid gap-3 px-5 py-4 md:grid-cols-[minmax(0,1.5fr)_minmax(0,1.1fr)_120px_120px_80px_100px]"
              >
                <Skeleton variant="text" className="h-4 w-28" />
                <Skeleton variant="text" className="h-4 w-24" />
                <Skeleton variant="text" className="h-4 w-16" />
                <Skeleton variant="text" className="h-4 w-16" />
                <Skeleton variant="text" className="h-4 w-12" />
                <Skeleton variant="text" className="h-4 w-14" />
              </div>
            ))}
          </div>
        </Surface>
      ) : filtered.length === 0 ? (
        <EmptyState
          icon={<Buildings size={40} weight="bold" />}
          title="No companies found"
          description="Adjust the validation filter or refresh the company registry."
        />
      ) : (
        <Surface padding="none">
          <div className="border-b-2 border-border px-5 py-5">
            <SectionHeader
              title="Company Registry"
              description="Validation state, ATS routing, and confidence signals for each canonical company."
              action={
                <div className="font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-text-muted">
                  {filtered.length} shown
                </div>
              }
            />
          </div>

          <div className="hidden border-b-2 border-border bg-[var(--color-bg-tertiary)] px-5 py-3 md:grid md:grid-cols-[minmax(0,1.5fr)_minmax(0,1.1fr)_120px_120px_80px_100px] md:gap-3">
            {["Company", "Domain", "ATS", "Status", "Jobs", "Confidence"].map((label) => (
              <div
                key={label}
                className={cn(
                  "font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-text-muted",
                  (label === "Jobs" || label === "Confidence") && "text-right"
                )}
              >
                {label}
              </div>
            ))}
          </div>

          <div className="divide-y-2 divide-border">
            {filtered.map((company: Company) => (
              <div
                key={company.id}
                className="grid gap-3 px-5 py-4 md:grid-cols-[minmax(0,1.5fr)_minmax(0,1.1fr)_120px_120px_80px_100px] md:items-center"
              >
                <div className="min-w-0">
                  <p className="text-lg font-black uppercase tracking-[-0.05em] text-text-primary">
                    {company.canonical_name}
                  </p>
                  <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-text-muted md:hidden">
                    <span className="inline-flex items-center gap-1">
                      <Globe size={12} />
                      Domain saved
                    </span>
                    <span>{company.ats_provider || "-"}</span>
                    <span>{company.job_count} jobs</span>
                  </div>
                </div>

                <div className="min-w-0">
                  <p className="font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-text-muted md:hidden">
                    Domain
                  </p>
                  <p className="truncate text-sm text-text-secondary">{company.domain || "-"}</p>
                </div>

                <div>
                  <p className="font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-text-muted md:hidden">
                    ATS
                  </p>
                  <p className="text-sm text-text-secondary">{company.ats_provider || "-"}</p>
                </div>

                <div>
                  <p className="font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-text-muted md:hidden">
                    Status
                  </p>
                  <Badge variant={companyStateVariant(company.validation_state)}>
                    {company.validation_state}
                  </Badge>
                </div>

                <div>
                  <p className="font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-text-muted md:hidden">
                    Jobs
                  </p>
                  <p className="text-sm text-text-secondary md:text-right">{company.job_count}</p>
                </div>

                <div>
                  <p className="font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-text-muted md:hidden">
                    Confidence
                  </p>
                  <p className="font-mono text-sm text-text-secondary md:text-right">
                    {(company.confidence_score * 100).toFixed(0)}%
                  </p>
                </div>
              </div>
            ))}
          </div>
        </Surface>
      )}
    </div>
  );
}
