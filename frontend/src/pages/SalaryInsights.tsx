import {
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
import { useMemo, useState } from "react";
import { salaryApi, type OfferEvaluation, type SalaryResearch } from "../api/salary";
import { MetricStrip } from "../components/system/MetricStrip";
import { PageHeader } from "../components/system/PageHeader";
import { SectionHeader } from "../components/system/SectionHeader";
import { SplitWorkspace } from "../components/system/SplitWorkspace";
import { StateBlock } from "../components/system/StateBlock";
import { Surface } from "../components/system/Surface";
import Badge from "../components/ui/Badge";
import Button from "../components/ui/Button";
import Input from "../components/ui/Input";
import Skeleton from "../components/ui/Skeleton";
import { toast } from "../components/ui/toastService";

interface SavedResearch {
  id: string;
  job_title: string;
  company: string;
  location: string;
  research: SalaryResearch;
  timestamp: string;
}

function formatSalary(value: number | null | undefined): string {
  if (!value) return "-";
  if (value >= 1000) {
    return `$${Math.round(value / 1000)}k`;
  }
  return `$${value.toLocaleString()}`;
}

function SalaryRangeBar({ research }: { research: SalaryResearch }) {
  const markers = [
    { label: "P25", value: research.p25 ?? 0, accent: "text-text-primary" },
    { label: "P50", value: research.p50 ?? 0, accent: "text-accent-primary" },
    { label: "P75", value: research.p75 ?? 0, accent: "text-text-primary" },
    { label: "P90", value: research.p90 ?? 0, accent: "text-text-primary" },
  ];
  const values = markers.map((marker) => marker.value).filter((value) => value > 0);
  if (values.length < 2) return null;

  const floor = Math.min(...values);
  const ceiling = Math.max(...values);
  const range = ceiling - floor;
  if (range <= 0) return null;

  const getPosition = (value: number) => ((value - floor) / range) * 100;

  return (
    <div className="space-y-5">
      <div className="relative h-12 border-2 border-border bg-[var(--color-bg-tertiary)] px-4">
        <div className="absolute left-4 right-4 top-1/2 h-2 -translate-y-1/2 bg-border" />
        <div
          className="absolute top-1/2 h-4 -translate-y-1/2 border-2 border-border bg-accent-primary/20"
          style={{
            left: `calc(${getPosition(research.p25 ?? floor)}% + 0.5rem)`,
            width: `${getPosition(research.p75 ?? ceiling) - getPosition(research.p25 ?? floor)}%`,
          }}
        />
        {markers.map((marker) => (
          <div
            key={marker.label}
            className="absolute top-1/2 size-4 -translate-y-1/2 border-2 border-border shadow-[var(--shadow-xs)]"
            style={{
              left: `calc(${getPosition(marker.value)}% + 0.5rem)`,
              backgroundColor:
                marker.label === "P50" ? "var(--color-accent-primary)" : "var(--card)",
            }}
          />
        ))}
      </div>

      <div className="grid grid-cols-2 gap-2 text-center sm:grid-cols-4">
        {markers.map((item) => (
          <div key={item.label} className="border-2 border-border bg-card px-2 py-3 shadow-[var(--shadow-xs)]">
            <p className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
              {item.label}
            </p>
            <p className={`mt-2 text-lg font-black uppercase tracking-[-0.05em] ${item.accent}`}>
              {formatSalary(item.value)}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}

function VerdictDisplay({ evaluation }: { evaluation: OfferEvaluation }) {
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <Badge variant="info" size="md">
          <Lightbulb size={14} weight="bold" />
          <span className="ml-1">Negotiation guidance</span>
        </Badge>
        {evaluation.counter_offer ? (
          <Badge variant="success" size="md">
            <ArrowUp size={14} weight="bold" />
            <span className="ml-1">Counter {formatSalary(evaluation.counter_offer)}</span>
          </Badge>
        ) : null}
        {evaluation.walkaway_point ? (
          <Badge variant="warning" size="md">
            <Minus size={14} weight="bold" />
            <span className="ml-1">Walkaway {formatSalary(evaluation.walkaway_point)}</span>
          </Badge>
        ) : null}
      </div>

      <div className="border-2 border-border bg-[var(--color-bg-tertiary)] px-4 py-4 text-sm leading-6 text-text-secondary shadow-[var(--shadow-xs)]">
        {evaluation.assessment}
      </div>

      {evaluation.talking_points.length ? (
        <div className="space-y-3">
          <h4 className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
            Talking points
          </h4>
          <div className="space-y-2">
            {evaluation.talking_points.map((tip, index) => (
              <div
                key={`${tip}-${index}`}
                className="border-2 border-border bg-[var(--color-bg-tertiary)] px-4 py-3 text-sm leading-6 text-text-secondary shadow-[var(--shadow-xs)]"
              >
                {tip}
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {evaluation.negotiation_script ? (
        <div className="space-y-3">
          <h4 className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
            Negotiation script
          </h4>
          <div className="border-2 border-border bg-card px-4 py-4 text-sm leading-6 text-text-secondary shadow-[var(--shadow-xs)]">
            {evaluation.negotiation_script}
          </div>
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
        icon: <Lightbulb size={18} weight="bold" />,
      },
      {
        key: "median",
        label: "Median",
        value: latestResearch ? formatSalary(latestResearch.p50) : "-",
        hint: "Most recent P50 market read.",
        icon: <CurrencyDollar size={18} weight="bold" />,
        tone: "warning" as const,
      },
      {
        key: "evaluation",
        label: "Counter offer",
        value: evaluation?.counter_offer ? formatSalary(evaluation.counter_offer) : "-",
        hint: "Negotiation anchor from the latest evaluation.",
        icon: <TrendUp size={18} weight="bold" />,
        tone: "success" as const,
      },
      {
        key: "company",
        label: "Company set",
        value: company || "None",
        hint: "Used for market comparisons.",
        icon: <Building size={18} weight="bold" />,
      },
    ],
    [company, evaluation?.counter_offer, latestResearch, savedResearches.length]
  );

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Prepare"
        title="Salary Insights"
        description="Research the market, pressure-test offers, and keep a negotiation log that works cleanly on desktop, tablet, and phone."
        meta={
          <div className="flex flex-wrap gap-2">
            <Badge variant="warning" size="sm">
              Market percentiles
            </Badge>
            <Badge variant="success" size="sm">
              Offer coaching
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
                title="Salary research"
                description="Pull a market range for the exact role, company, and location under consideration."
              />
              <div className="mt-6 grid gap-4 xl:grid-cols-2">
                <Input
                  label="Job title"
                  value={jobTitle}
                  onChange={(event) => setJobTitle(event.target.value)}
                  placeholder="Senior Frontend Engineer"
                  icon={<MagnifyingGlass size={16} weight="bold" />}
                />
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
                <div className="flex items-end">
                  <Button
                    className="w-full"
                    onClick={() => researchMutation.mutate()}
                    loading={researchMutation.isPending}
                    disabled={!jobTitle.trim()}
                    icon={<TrendUp size={16} weight="bold" />}
                  >
                    Research salary
                  </Button>
                </div>
              </div>
            </Surface>

            {researchMutation.isPending ? (
              <Surface tone="default" padding="lg" radius="xl">
                <Skeleton variant="text" className="h-5 w-1/3" />
                <Skeleton variant="rect" className="mt-6 h-32 w-full" />
              </Surface>
            ) : latestResearch ? (
              <Surface tone="default" padding="lg" radius="xl">
                <SectionHeader
                  title="Range view"
                  description={`Backend market percentiles returned in ${latestResearch.currency}${latestResearch.cached ? " from cache" : ""}.`}
                />
                <div className="mt-6 space-y-6">
                  <Surface tone="subtle" padding="md" radius="xl">
                    <div className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
                      Active query
                    </div>
                    <div className="mt-3 text-3xl font-black uppercase tracking-[-0.06em] text-text-primary">
                      {company || location ? "Market snapshot loaded" : "General market snapshot"}
                    </div>
                    <p className="mt-2 text-sm leading-6 text-text-secondary">
                      {[company || null, location || null].filter(Boolean).join(" / ") || "General market snapshot"}
                    </p>
                  </Surface>
                  <SalaryRangeBar research={latestResearch} />
                  {latestResearch.competing_companies.length ? (
                    <div className="space-y-3">
                      <div className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
                        Competing companies
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {latestResearch.competing_companies.map((entry) => (
                          <Badge key={entry} variant="info" size="sm">
                            {entry}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  ) : null}
                  {latestResearch.yoe_brackets.length ? (
                    <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                      {latestResearch.yoe_brackets.map((entry) => (
                        <div key={entry.years} className="border-2 border-border bg-card px-4 py-4 shadow-[var(--shadow-xs)]">
                          <div className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
                            {entry.years}
                          </div>
                          <div className="mt-3 text-lg font-black uppercase tracking-[-0.04em] text-text-primary">
                            {entry.range}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : null}
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

            <Surface tone="default" padding="lg" radius="xl">
              <SectionHeader
                title="Offer evaluation"
                description="Compare a concrete offer against the latest market context."
              />
              <div className="mt-6 grid gap-4 xl:grid-cols-[minmax(0,1fr)_220px]">
                <Input
                  label="Offer amount"
                  type="number"
                  value={offerAmount}
                  onChange={(event) => setOfferAmount(event.target.value)}
                  placeholder="150000"
                  icon={<CurrencyDollar size={16} weight="bold" />}
                />
                <div className="flex items-end">
                  <Button
                    variant="success"
                    className="w-full"
                    onClick={() => evaluateMutation.mutate()}
                    loading={evaluateMutation.isPending}
                    disabled={!jobTitle.trim() || !offerAmount || Number(offerAmount) <= 0}
                    icon={<TrendUp size={16} weight="bold" />}
                  >
                    Evaluate offer
                  </Button>
                </div>
              </div>

              {evaluateMutation.isPending ? <Skeleton variant="rect" className="mt-6 h-24 w-full" /> : null}
              {evaluation ? (
                <div className="mt-6">
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
                    <div className="space-y-3">
                      <div>
                        <div className="text-lg font-black uppercase tracking-[-0.04em] text-text-primary">
                          {saved.job_title}
                        </div>
                        <p className="mt-1 text-sm leading-6 text-text-secondary">
                          {[saved.company || null, saved.location || null].filter(Boolean).join(" / ") || "General market"}
                        </p>
                      </div>
                      <div className="flex items-center justify-between gap-3">
                        <span className="text-2xl font-black uppercase tracking-[-0.05em] text-accent-primary">
                          {formatSalary(saved.research.p50)}
                        </span>
                        <span className="text-sm text-muted-foreground">{format(new Date(saved.timestamp), "PP")}</span>
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
              description="Use P50 as the anchor, P25/P75 as the bracket, and the coaching output as the negotiation plan."
            />
          </div>
        }
      />
    </div>
  );
}
