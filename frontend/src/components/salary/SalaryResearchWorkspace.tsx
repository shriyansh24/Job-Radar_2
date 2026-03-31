import { Building, CurrencyDollar, MagnifyingGlass, MapPin, TrendUp } from "@phosphor-icons/react";
import { type SalaryResearch } from "../../api/salary";
import { SectionHeader } from "../system/SectionHeader";
import { StateBlock } from "../system/StateBlock";
import { Surface } from "../system/Surface";
import Button from "../ui/Button";
import Input from "../ui/Input";
import Skeleton from "../ui/Skeleton";
import { SalaryRangeBar } from "./SalaryWidgets";

export function SalaryResearchWorkspace({
  jobTitle,
  company,
  location,
  latestResearch,
  isPending,
  onJobTitleChange,
  onCompanyChange,
  onLocationChange,
  onResearch,
}: {
  jobTitle: string;
  company: string;
  location: string;
  latestResearch: SalaryResearch | null;
  isPending: boolean;
  onJobTitleChange: (value: string) => void;
  onCompanyChange: (value: string) => void;
  onLocationChange: (value: string) => void;
  onResearch: () => void;
}) {
  const querySummary = [company || null, location || null].filter(Boolean).join(" / ") || "General market snapshot";

  return (
    <div className="space-y-6">
      <Surface tone="default" padding="lg" radius="xl" className="hero-panel">
        <SectionHeader title="Salary research" description="Pull a market range for the current role." />
        <div className="mt-6 grid gap-4 xl:grid-cols-2">
          <Input
            label="Job title"
            value={jobTitle}
            onChange={(event) => onJobTitleChange(event.target.value)}
            placeholder="Senior Frontend Engineer"
            icon={<MagnifyingGlass size={16} weight="bold" />}
          />
          <Input
            label="Company"
            value={company}
            onChange={(event) => onCompanyChange(event.target.value)}
            placeholder="Stripe"
            icon={<Building size={16} weight="bold" />}
          />
          <Input
            label="Location"
            value={location}
            onChange={(event) => onLocationChange(event.target.value)}
            placeholder="Remote"
            icon={<MapPin size={16} weight="bold" />}
          />
          <div className="flex items-end">
            <Button
              className="w-full"
              onClick={onResearch}
              loading={isPending}
              disabled={!jobTitle.trim()}
              icon={<TrendUp size={16} weight="bold" />}
            >
              Research
            </Button>
          </div>
        </div>
      </Surface>

      {isPending ? (
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
              <p className="mt-2 text-sm leading-6 text-text-secondary">{querySummary}</p>
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
    </div>
  );
}
