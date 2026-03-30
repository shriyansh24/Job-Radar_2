import { Building, CurrencyDollar, Lightbulb, MapPin, MagnifyingGlass, TrendUp } from "@phosphor-icons/react";
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
import Button from "../components/ui/Button";
import Input from "../components/ui/Input";
import Skeleton from "../components/ui/Skeleton";
import { toast } from "../components/ui/toastService";
import {
  SalaryRangeBar,
  SalarySavedResearchCard,
  SalaryScopeRail,
  SalaryVerdictDisplay,
} from "../components/salary/SalaryWidgets";

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
  if (value >= 1000) return `$${Math.round(value / 1000)}k`;
  return `$${value.toLocaleString()}`;
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
        hint: "Recent salary reads.",
        icon: <Lightbulb size={18} weight="bold" />,
      },
      {
        key: "median",
        label: "Median",
        value: latestResearch ? formatSalary(latestResearch.p50) : "-",
        hint: "Latest P50 read.",
        icon: <CurrencyDollar size={18} weight="bold" />,
        tone: "warning" as const,
      },
      {
        key: "evaluation",
        label: "Counter offer",
        value: evaluation?.counter_offer ? formatSalary(evaluation.counter_offer) : "-",
        hint: "Negotiation anchor.",
        icon: <TrendUp size={18} weight="bold" />,
        tone: "success" as const,
      },
      {
        key: "company",
        label: "Company",
        value: company || "None",
        hint: "Used for comparisons.",
        icon: <Building size={18} weight="bold" />,
      },
    ],
    [company, evaluation?.counter_offer, latestResearch, savedResearches.length]
  );

  return (
    <div className="space-y-6">
      <PageHeader
        className="hero-panel"
        eyebrow="Prepare"
        title="Salary Insights"
        description="Research a market range and compare a live offer against it."
        meta={
          <div className="flex flex-wrap gap-2">
            <span className="border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-tertiary)] px-3 py-2 font-mono text-[10px] font-bold uppercase tracking-[0.16em]">
              Market range
            </span>
            <span className="border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-tertiary)] px-3 py-2 font-mono text-[10px] font-bold uppercase tracking-[0.16em]">
              Offer guidance
            </span>
          </div>
        }
      />

      <MetricStrip items={metrics} />

      <SplitWorkspace
        primary={
          <div className="space-y-6">
            <Surface tone="default" padding="lg" radius="xl" className="hero-panel">
              <SectionHeader title="Salary research" description="Pull a market range for the current role." />
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
                    Research
                  </Button>
                </div>
              </div>
            </Surface>

            {researchMutation.isPending ? (
              <Surface tone="default" padding="lg" radius="xl" className="brutal-panel">
                <Skeleton variant="text" className="h-5 w-1/3" />
                <Skeleton variant="rect" className="mt-6 h-32 w-full" />
              </Surface>
            ) : latestResearch ? (
              <Surface tone="default" padding="lg" radius="xl">
                <SectionHeader
                  title="Range view"
                  description={`Backend percentiles returned in ${latestResearch.currency}${latestResearch.cached ? " from cache" : ""}.`}
                />
                <div className="mt-6 space-y-6">
                  <Surface tone="subtle" padding="md" radius="xl" className="hero-panel">
                    <div className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
                      Query
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
                          <span key={entry} className="border-2 border-border px-3 py-2 text-xs uppercase tracking-[0.14em]">
                            {entry}
                          </span>
                        ))}
                      </div>
                    </div>
                  ) : null}
                  {latestResearch.yoe_brackets.length ? (
                    <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                      {latestResearch.yoe_brackets.map((entry) => (
                        <div key={entry.years} className="brutal-panel px-4 py-4">
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
                description="Research a job title to see the market range."
              />
            )}

            <Surface tone="default" padding="lg" radius="xl" className="hero-panel">
              <SectionHeader title="Offer evaluation" description="Compare an offer against the latest market context." />
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
                    Evaluate
                  </Button>
                </div>
              </div>

              {evaluateMutation.isPending ? <Skeleton variant="rect" className="mt-6 h-24 w-full" /> : null}
              {evaluation ? (
                <div className="mt-6">
                  <SalaryVerdictDisplay evaluation={evaluation as OfferEvaluation} />
                </div>
              ) : null}
            </Surface>
          </div>
        }
        secondary={
          <div className="space-y-4">
            {savedResearches.length ? (
              savedResearches.map((saved) => (
                <SalarySavedResearchCard
                  key={saved.id}
                  title={saved.job_title}
                  company={saved.company}
                  location={saved.location}
                  market={formatSalary(saved.research.p50)}
                  timestamp={format(new Date(saved.timestamp), "PP")}
                  onSelect={() => {
                    setJobTitle(saved.job_title);
                    setCompany(saved.company);
                    setLocation(saved.location);
                  }}
                />
              ))
            ) : (
              <StateBlock
                tone="muted"
                icon={<Lightbulb size={18} weight="bold" />}
                title="Recent research"
                description="Saved salary pulls and offer evaluations will collect here."
              />
            )}
            <SalaryScopeRail
              title="Reading the result"
              description="Use P50 as the anchor, P25/P75 as the bracket, and the coaching output as the plan."
            />
          </div>
        }
      />
    </div>
  );
}
