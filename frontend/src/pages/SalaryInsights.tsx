import {
  ArrowDown,
  ArrowUp,
  Building,
  CurrencyDollar,
  Lightbulb,
  MagnifyingGlass,
  MapPin,
  Minus,
  TrendUp,
} from "@phosphor-icons/react";
import { useMutation } from "@tanstack/react-query";
import { format } from "date-fns";
import { useMemo, useState, type ReactNode } from "react";
import { salaryApi, type OfferEvaluation, type SalaryResearch } from "../api/salary";
import Badge from "../components/ui/Badge";
import Button from "../components/ui/Button";
import Input from "../components/ui/Input";
import Skeleton from "../components/ui/Skeleton";
import { MetricStrip } from "../components/system/MetricStrip";
import { PageHeader } from "../components/system/PageHeader";
import { SectionHeader } from "../components/system/SectionHeader";
import { SplitWorkspace } from "../components/system/SplitWorkspace";
import { StateBlock } from "../components/system/StateBlock";
import { Surface } from "../components/system/Surface";
import { toast } from "../components/ui/toastService";

interface SavedResearch {
  id: string;
  job_title: string;
  company: string;
  location: string;
  research: SalaryResearch;
  timestamp: string;
}

function formatSalary(value: number): string {
  if (value >= 1000) {
    return `$${Math.round(value / 1000)}k`;
  }
  return `$${value.toLocaleString()}`;
}

function SalaryRangeBar({ research }: { research: SalaryResearch }) {
  const min = research.min_salary ?? 0;
  const p25 = research.percentile_25 ?? 0;
  const median = research.median_salary ?? 0;
  const p75 = research.percentile_75 ?? 0;
  const max = research.max_salary ?? 0;
  const range = max - min;

  if (range <= 0) return null;

  const getPosition = (value: number) => ((value - min) / range) * 100;

  return (
    <div className="space-y-4">
      <div className="relative h-8">
        <div className="absolute top-1/2 h-2 w-full -translate-y-1/2 rounded-full bg-border/70" />
        <div
          className="absolute top-1/2 h-2 -translate-y-1/2 rounded-full bg-[var(--color-accent-primary)]/25"
          style={{
            left: `${getPosition(p25)}%`,
            width: `${getPosition(p75) - getPosition(p25)}%`,
          }}
        />
        <div className="absolute left-0 top-1/2 size-3 -translate-y-1/2 rounded-full border-2 border-background bg-muted-foreground" />
        <div
          className="absolute top-1/2 size-3 -translate-y-1/2 rounded-full border-2 border-background bg-[var(--color-accent-primary)]/60"
          style={{ left: `${getPosition(p25)}%` }}
        />
        <div
          className="absolute top-1/2 z-10 size-4 -translate-y-1/2 rounded-full border-2 border-background bg-[var(--color-accent-primary)]"
          style={{ left: `${getPosition(median)}%` }}
        />
        <div
          className="absolute top-1/2 size-3 -translate-y-1/2 rounded-full border-2 border-background bg-[var(--color-accent-primary)]/60"
          style={{ left: `${getPosition(p75)}%` }}
        />
        <div className="absolute left-full top-1/2 size-3 -translate-y-1/2 rounded-full border-2 border-background bg-muted-foreground" />
      </div>

      <div className="grid grid-cols-5 gap-2 text-center text-sm">
        <div>
          <p className="text-xs text-muted-foreground">Min</p>
          <p className="font-medium text-foreground">{formatSalary(min)}</p>
        </div>
        <div>
          <p className="text-xs text-muted-foreground">P25</p>
          <p className="font-medium text-foreground">{formatSalary(p25)}</p>
        </div>
        <div>
          <p className="text-xs font-medium text-[var(--color-accent-primary)]">Median</p>
          <p className="font-semibold text-[var(--color-accent-primary)]">{formatSalary(median)}</p>
        </div>
        <div>
          <p className="text-xs text-muted-foreground">P75</p>
          <p className="font-medium text-foreground">{formatSalary(p75)}</p>
        </div>
        <div>
          <p className="text-xs text-muted-foreground">Max</p>
          <p className="font-medium text-foreground">{formatSalary(max)}</p>
        </div>
      </div>
    </div>
  );
}

function VerdictDisplay({ evaluation }: { evaluation: OfferEvaluation }) {
  const verdictConfig: Record<
    "above" | "at" | "below",
    { icon: ReactNode; variant: "success" | "warning" | "danger"; label: string }
  > = {
    above: { icon: <ArrowUp size={16} weight="bold" />, variant: "success", label: "Above Market" },
    at: { icon: <Minus size={16} weight="bold" />, variant: "warning", label: "At Market" },
    below: { icon: <ArrowDown size={16} weight="bold" />, variant: "danger", label: "Below Market" },
  };

  const rating = evaluation.overall_rating === "above_market" ? "above" : evaluation.overall_rating === "below_market" ? "below" : "at";
  const config = verdictConfig[rating];

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <Badge variant={config.variant} size="md">
          {config.icon}
          <span className="ml-1">{config.label}</span>
        </Badge>
        <span className="text-sm text-muted-foreground">
          Percentile <span className="font-semibold text-foreground">{evaluation.percentile}th</span>
        </span>
      </div>

      {evaluation.negotiation_tips?.length ? (
        <div className="space-y-2">
          <h4 className="text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground">Tips</h4>
          <ul className="space-y-1.5">
            {evaluation.negotiation_tips.map((tip, index) => (
              <li key={index} className="flex items-start gap-2 text-sm text-foreground">
                <span className="mt-1 text-[var(--color-accent-primary)]">•</span>
                <span className="leading-6 text-muted-foreground">{tip}</span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}

export default function SalaryInsights() {
  const [jobTitle, setJobTitle] = useState("");
  const [company, setCompany] = useState("");
  const [location, setLocation] = useState("");
  const [offerAmount, setOfferAmount] = useState("");
  const [savedResearches, setSavedResearches] = useState<SavedResearch[]>([]);

  const researchMutation = useMutation({
    mutationFn: () =>
      salaryApi
        .research({
          job_title: jobTitle,
          company_name: company || undefined,
          location: location || undefined,
        })
        .then((response) => response.data),
    onSuccess: (research) => {
      toast("success", "Salary research complete");
      setSavedResearches((current) => [
        {
          id: crypto.randomUUID(),
          job_title: jobTitle,
          company,
          location,
          research,
          timestamp: new Date().toISOString(),
        },
        ...current,
      ]);
    },
    onError: () => toast("error", "Research failed"),
  });

  const evaluateMutation = useMutation({
    mutationFn: () =>
      salaryApi
        .evaluateOffer({
          job_title: jobTitle,
          offered_salary: Number(offerAmount),
          company_name: company || undefined,
          location: location || undefined,
        })
        .then((response) => response.data),
    onSuccess: () => toast("success", "Offer evaluated"),
    onError: () => toast("error", "Evaluation failed"),
  });

  const latestResearch = researchMutation.data ?? null;
  const evaluation = evaluateMutation.data ?? null;

  const metrics = useMemo(
    () => [
      {
        key: "saved",
        label: "Saved research",
        value: savedResearches.length,
        hint: "Recent salary reads that can be reused later.",
      },
      {
        key: "median",
        label: "Latest median",
        value: latestResearch ? formatSalary(latestResearch.median_salary ?? 0) : "—",
        hint: "Most recent median salary pull.",
      },
      {
        key: "evaluation",
        label: "Evaluation",
        value: evaluation ? `${evaluation.percentile}th` : "—",
        hint: "Where the offer lands relative to market.",
      },
      {
        key: "company",
        label: "Company set",
        value: company || "None",
        hint: "Used for market comparisons.",
      },
    ],
    [company, evaluation, latestResearch, savedResearches.length]
  );

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Prepare"
        title="Salary Insights"
        description="Research the market, compare offers, and keep a lightweight record of the numbers that matter."
      />

      <MetricStrip items={metrics} />

      <SplitWorkspace
        primary={
          <div className="space-y-6">
            <Surface tone="default" padding="md" radius="xl">
              <SectionHeader
                title="Salary research"
                description="Pull a market range for the role, company, and location you care about."
              />
              <div className="mt-4 space-y-4">
                <Input
                  label="Job title"
                  value={jobTitle}
                  onChange={(event) => setJobTitle(event.target.value)}
                  placeholder="Senior Frontend Engineer"
                  icon={<MagnifyingGlass size={16} weight="bold" />}
                />
                <div className="grid gap-4 md:grid-cols-2">
                  <Input
                    label="Company"
                    value={company}
                    onChange={(event) => setCompany(event.target.value)}
                    placeholder="Stripe"
                    icon={<Building size={16} weight="bold" />}
                  />
                  <Input
                    label="Location"
                    value={location}
                    onChange={(event) => setLocation(event.target.value)}
                    placeholder="Remote"
                    icon={<MapPin size={16} weight="bold" />}
                  />
                </div>
                <Button
                  onClick={() => researchMutation.mutate()}
                  loading={researchMutation.isPending}
                  disabled={!jobTitle.trim()}
                  icon={<TrendUp size={16} weight="bold" />}
                >
                  Research salary
                </Button>
              </div>
            </Surface>

            {researchMutation.isPending ? (
              <Surface tone="default" padding="md" radius="xl">
                <Skeleton variant="text" className="mb-4 h-5 w-1/2" />
                <Skeleton variant="rect" className="h-24 w-full" />
              </Surface>
            ) : latestResearch ? (
              <Surface tone="default" padding="md" radius="xl">
                <SectionHeader
                  title="Range view"
                  description={`Based on ${latestResearch.data_sources.length} sources and currency ${latestResearch.currency}.`}
                />
                <div className="mt-4">
                  <SalaryRangeBar research={latestResearch} />
                </div>
              </Surface>
            ) : (
              <StateBlock
                tone="muted"
                icon={<CurrencyDollar size={18} weight="bold" />}
                title="No research yet"
                description="Research a job title to see the market distribution."
              />
            )}

            <Surface tone="default" padding="md" radius="xl">
              <SectionHeader
                title="Offer evaluation"
                description="Compare a concrete offer against the market range."
              />
              <div className="mt-4 space-y-4">
                <Input
                  label="Offer amount"
                  type="number"
                  value={offerAmount}
                  onChange={(event) => setOfferAmount(event.target.value)}
                  placeholder="150000"
                  icon={<CurrencyDollar size={16} weight="bold" />}
                />
                <Button
                  variant="success"
                  onClick={() => evaluateMutation.mutate()}
                  loading={evaluateMutation.isPending}
                  disabled={!jobTitle.trim() || !offerAmount || Number(offerAmount) <= 0}
                  icon={<TrendUp size={16} weight="bold" />}
                >
                  Evaluate offer
                </Button>
              </div>

              {evaluateMutation.isPending ? (
                <Skeleton variant="rect" className="mt-4 h-20 w-full" />
              ) : evaluation ? (
                <div className="mt-4">
                  <VerdictDisplay evaluation={evaluation} />
                </div>
              ) : null}
            </Surface>
          </div>
        }
        secondary={
          <div className="space-y-4">
            {savedResearches.length ? (
              savedResearches.map((saved) => (
                <Surface key={saved.id} tone="default" padding="md" radius="xl" interactive>
                  <button
                    type="button"
                    className="block w-full text-left"
                    onClick={() => {
                      setJobTitle(saved.job_title);
                      setCompany(saved.company);
                      setLocation(saved.location);
                    }}
                  >
                    <div className="space-y-2">
                      <div className="text-sm font-semibold tracking-[-0.01em]">{saved.job_title}</div>
                      <div className="flex flex-wrap gap-2 text-xs text-muted-foreground">
                        {saved.company ? <span>{saved.company}</span> : null}
                        {saved.location ? <span>{saved.location}</span> : null}
                      </div>
                      <div className="flex items-center justify-between gap-3">
                        <span className="text-sm font-semibold text-[var(--color-accent-primary)]">
                          {formatSalary(saved.research.median_salary ?? 0)}
                        </span>
                        <span className="text-xs text-muted-foreground">
                          {format(new Date(saved.timestamp), "PP")}
                        </span>
                      </div>
                    </div>
                  </button>
                </Surface>
              ))
            ) : (
              <StateBlock
                tone="muted"
                icon={<Lightbulb size={18} weight="bold" />}
                title="Recent research"
                description="Your most recent salary pulls and offer evaluations will collect here."
              />
            )}
            <StateBlock
              tone="warning"
              icon={<Lightbulb size={18} weight="bold" />}
              title="Reading the result"
              description="Use the median as the anchor, the band as context, and the percentile as the negotiation signal."
            />
          </div>
        }
      />
    </div>
  );
}
