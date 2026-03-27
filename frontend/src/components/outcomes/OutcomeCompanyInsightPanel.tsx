import { Buildings, ChartBar, Ghost } from "@phosphor-icons/react";
import type { CompanyInsight } from "../../api/outcomes";
import Badge from "../ui/Badge";
import { Button } from "../ui/Button";
import EmptyState from "../ui/EmptyState";
import Input from "../ui/Input";
import Skeleton from "../ui/Skeleton";
import { SectionHeader } from "../system/SectionHeader";
import { Surface } from "../system/Surface";
import { InsightTile } from "./InsightTile";

export function OutcomeCompanyInsightPanel({
  companyQuery,
  setCompanyQuery,
  companyInsight,
  loading,
  onLookup,
}: {
  companyQuery: string;
  setCompanyQuery: (value: string) => void;
  companyInsight: CompanyInsight | null;
  loading: boolean;
  onLookup: () => void;
}) {
  return (
    <Surface tone="default" padding="lg" radius="xl">
      <SectionHeader
        title="Company insight lookup"
        description="Pull a company view to see whether the pattern is you, the company, or the stage."
        action={<Badge variant="info">Single target view</Badge>}
      />
      <div className="mt-4 flex flex-col gap-3 sm:flex-row">
        <Input
          value={companyQuery}
          onChange={(event) => setCompanyQuery(event.target.value)}
          placeholder="Search a company"
          icon={<Buildings size={16} weight="bold" />}
        />
        <Button
          variant="secondary"
          onClick={onLookup}
          disabled={!companyQuery.trim() || loading}
          icon={<ChartBar size={16} weight="bold" />}
        >
          Lookup
        </Button>
      </div>

      <div className="mt-5 border-t-2 border-border pt-5">
        {loading ? (
          <div className="space-y-3">
            <Skeleton variant="rect" className="h-24 w-full" />
            <Skeleton variant="rect" className="h-20 w-full" />
            <Skeleton variant="rect" className="h-20 w-full" />
          </div>
        ) : companyInsight ? (
          <div className="space-y-4">
            <div className="border-2 border-border bg-[var(--color-accent-primary-subtle)] p-4">
              <div className="text-lg font-black tracking-[-0.04em] text-text-primary">
                {companyInsight.company_name}
              </div>
              <p className="mt-1 text-sm text-text-secondary">
                {companyInsight.total_applications} applications tracked across this company.
              </p>
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              <InsightTile
                label="Callback Rate"
                value={`${Math.round((companyInsight.callback_count / Math.max(companyInsight.total_applications, 1)) * 100)}%`}
                hint="Callbacks relative to total applications."
              />
              <InsightTile
                label="Ghost Rate"
                value={`${Math.round(companyInsight.ghost_rate * 100)}%`}
                hint="How often the process went silent."
              />
              <InsightTile
                label="Offer Rate"
                value={`${Math.round(companyInsight.offer_rate * 100)}%`}
                hint="Offer conversion for this company."
              />
              <InsightTile
                label="Avg Response"
                value={companyInsight.avg_response_days !== null ? `${companyInsight.avg_response_days.toFixed(1)}d` : "N/A"}
                hint="Average days to a response."
              />
            </div>

            {companyInsight.culture_notes ? (
              <div className="border-2 border-border bg-[var(--color-bg-secondary)] p-4 text-sm leading-6 text-text-secondary">
                {companyInsight.culture_notes}
              </div>
            ) : null}
            {companyInsight.last_applied_at ? (
              <div className="text-xs text-muted-foreground">
                Last applied {new Date(companyInsight.last_applied_at).toLocaleDateString()}
              </div>
            ) : null}
          </div>
        ) : (
          <EmptyState
            icon={<Ghost size={30} weight="bold" />}
            title="No company insight selected"
            description="Run a lookup to see company-level response patterns and notes."
          />
        )}
      </div>
    </Surface>
  );
}
