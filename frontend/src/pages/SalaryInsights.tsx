import { Building, CurrencyDollar, Lightbulb, TrendUp } from "@phosphor-icons/react";
import { useMutation } from "@tanstack/react-query";
import { format } from "date-fns";
import { useMemo, useState } from "react";
import { salaryApi, type OfferEvaluation, type SalaryResearch } from "../api/salary";
import { SalaryOfferWorkspace } from "../components/salary/SalaryOfferWorkspace";
import { SalaryResearchWorkspace } from "../components/salary/SalaryResearchWorkspace";
import {
  SalarySavedResearchRail,
  type SalarySavedResearchRailEntry,
} from "../components/salary/SalarySavedResearchRail";
import { MetricStrip } from "../components/system/MetricStrip";
import { PageHeader } from "../components/system/PageHeader";
import { SplitWorkspace } from "../components/system/SplitWorkspace";
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
  const savedResearchEntries = useMemo<SalarySavedResearchRailEntry[]>(
    () =>
      savedResearches.map((saved) => ({
        id: saved.id,
        title: saved.job_title,
        company: saved.company,
        location: saved.location,
        market: formatSalary(saved.research.p50),
        timestamp: format(new Date(saved.timestamp), "PP"),
      })),
    [savedResearches]
  );

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
            <SalaryResearchWorkspace
              jobTitle={jobTitle}
              company={company}
              location={location}
              latestResearch={latestResearch}
              isPending={researchMutation.isPending}
              onJobTitleChange={setJobTitle}
              onCompanyChange={setCompany}
              onLocationChange={setLocation}
              onResearch={() => researchMutation.mutate()}
            />

            <SalaryOfferWorkspace
              jobTitle={jobTitle}
              offerAmount={offerAmount}
              evaluation={evaluation as OfferEvaluation | null}
              isPending={evaluateMutation.isPending}
              onOfferAmountChange={setOfferAmount}
              onEvaluate={() => evaluateMutation.mutate()}
            />
          </div>
        }
        secondary={
          <SalarySavedResearchRail
            entries={savedResearchEntries}
            onSelect={(entryId) => {
              const saved = savedResearches.find((entry) => entry.id === entryId);
              if (!saved) {
                return;
              }

              setJobTitle(saved.job_title);
              setCompany(saved.company);
              setLocation(saved.location);
            }}
          />
        }
      />
    </div>
  );
}
