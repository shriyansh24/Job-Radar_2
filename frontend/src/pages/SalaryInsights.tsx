import {
  Clock,
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
import { useState } from "react";
import { salaryApi, type OfferEvaluation, type SalaryResearch } from "../api/salary";
import Badge from "../components/ui/Badge";
import Button from "../components/ui/Button";
import Card from "../components/ui/Card";
import EmptyState from "../components/ui/EmptyState";
import Input from "../components/ui/Input";
import Skeleton from "../components/ui/Skeleton";
import { toast } from "../components/ui/toastService";
import { cn } from "../lib/utils";

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
    return `$${(value / 1000).toFixed(0)}k`;
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
      <div className="flex items-center justify-between text-xs text-text-muted">
        <span>Min</span>
        <span>Max</span>
      </div>

      <div className="relative h-8">
        {/* Full range track */}
        <div className="absolute top-1/2 -translate-y-1/2 w-full h-2 bg-bg-tertiary rounded-full" />

        {/* P25-P75 range (interquartile) */}
        <div
          className="absolute top-1/2 -translate-y-1/2 h-2 bg-accent-primary/30 rounded-full"
          style={{
            left: `${getPosition(p25)}%`,
            width: `${getPosition(p75) - getPosition(p25)}%`,
          }}
        />

        {/* Min marker */}
        <div
          className="absolute top-1/2 -translate-y-1/2 w-3 h-3 rounded-full bg-text-muted border-2 border-bg-secondary"
          style={{ left: '0%', transform: 'translate(-50%, -50%)' }}
        />

        {/* P25 marker */}
        <div
          className="absolute top-1/2 -translate-y-1/2 w-3 h-3 rounded-full bg-accent-primary/60 border-2 border-bg-secondary"
          style={{ left: `${getPosition(p25)}%`, transform: 'translate(-50%, -50%)' }}
        />

        {/* Median marker */}
        <div
          className="absolute top-1/2 -translate-y-1/2 w-4 h-4 rounded-full bg-accent-primary border-2 border-bg-secondary z-10"
          style={{ left: `${getPosition(median)}%`, transform: 'translate(-50%, -50%)' }}
        />

        {/* P75 marker */}
        <div
          className="absolute top-1/2 -translate-y-1/2 w-3 h-3 rounded-full bg-accent-primary/60 border-2 border-bg-secondary"
          style={{ left: `${getPosition(p75)}%`, transform: 'translate(-50%, -50%)' }}
        />

        {/* Max marker */}
        <div
          className="absolute top-1/2 -translate-y-1/2 w-3 h-3 rounded-full bg-text-muted border-2 border-bg-secondary"
          style={{ left: '100%', transform: 'translate(-50%, -50%)' }}
        />
      </div>

      {/* Value labels */}
      <div className="grid grid-cols-5 text-center">
        <div>
          <p className="text-xs text-text-muted">Min</p>
          <p className="text-sm font-medium text-text-primary">{formatSalary(min)}</p>
        </div>
        <div>
          <p className="text-xs text-text-muted">P25</p>
          <p className="text-sm font-medium text-text-primary">{formatSalary(p25)}</p>
        </div>
        <div>
          <p className="text-xs text-accent-primary font-medium">Median</p>
          <p className="text-sm font-bold text-accent-primary">{formatSalary(median)}</p>
        </div>
        <div>
          <p className="text-xs text-text-muted">P75</p>
          <p className="text-sm font-medium text-text-primary">{formatSalary(p75)}</p>
        </div>
        <div>
          <p className="text-xs text-text-muted">Max</p>
          <p className="text-sm font-medium text-text-primary">{formatSalary(max)}</p>
        </div>
      </div>
    </div>
  );
}

function VerdictDisplay({ evaluation }: { evaluation: OfferEvaluation }) {
  const verdictConfig: Record<string, { icon: React.ReactNode; variant: 'success' | 'warning' | 'danger'; label: string }> = {
    above: {
      icon: <ArrowUp size={16} weight="bold" />,
      variant: 'success',
      label: 'Above Market',
    },
    at: {
      icon: <Minus size={16} weight="bold" />,
      variant: 'warning',
      label: 'At Market',
    },
    below: {
      icon: <ArrowDown size={16} weight="bold" />,
      variant: 'danger',
      label: 'Below Market',
    },
  };

  const ratingToVerdict: Record<string, string> = { above_market: 'above', at_market: 'at', below_market: 'below' };
  const config = verdictConfig[ratingToVerdict[evaluation.overall_rating] ?? 'at'] || verdictConfig.at;

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <Badge variant={config.variant} size="md">
          {config.icon}
          <span className="ml-1">{config.label}</span>
        </Badge>
        <span className="text-sm text-text-secondary">
          Percentile: <span className="font-semibold text-text-primary">{evaluation.percentile}th</span>
        </span>
      </div>

      {evaluation.negotiation_tips && evaluation.negotiation_tips.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-xs font-medium text-text-secondary flex items-center gap-1.5">
            <Lightbulb size={12} weight="fill" className="text-accent-warning" />
            Tips
          </h4>
          <ul className="space-y-1.5">
            {evaluation.negotiation_tips.map((tip, i) => (
              <li key={i} className="text-sm text-text-primary flex items-start gap-2">
                <span className="text-accent-primary mt-1 shrink-0">&#8226;</span>
                {tip}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default function SalaryInsights() {
  const [jobTitle, setJobTitle] = useState('');
  const [company, setCompany] = useState('');
  const [location, setLocation] = useState('');
  const [offerAmount, setOfferAmount] = useState('');
  const [savedResearches, setSavedResearches] = useState<SavedResearch[]>([]);

  const researchMutation = useMutation({
    mutationFn: () =>
      salaryApi.research({
        job_title: jobTitle,
        company_name: company || undefined,
        location: location || undefined,
      }),
    onSuccess: (res) => {
      toast('success', 'Salary research complete');
      setSavedResearches((prev) => [
        {
          id: crypto.randomUUID(),
          job_title: jobTitle,
          company,
          location,
          research: res.data,
          timestamp: new Date().toISOString(),
        },
        ...prev,
      ]);
    },
    onError: () => toast('error', 'Research failed. Try again.'),
  });

  const evaluateMutation = useMutation({
    mutationFn: () =>
      salaryApi.evaluateOffer({
        job_title: jobTitle,
        offered_salary: Number(offerAmount),
        company_name: company || undefined,
        location: location || undefined,
      }),
    onSuccess: () => {
      toast('success', 'Offer evaluated');
    },
    onError: () => toast('error', 'Evaluation failed. Research a salary first.'),
  });

  const latestResearch = researchMutation.data?.data ?? null;
  const evaluation = evaluateMutation.data?.data ?? null;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-text-primary">Salary Insights</h1>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column: Research */}
        <div className="space-y-6">
          <Card>
            <h2 className="text-sm font-semibold text-text-primary mb-4 flex items-center gap-2">
              <MagnifyingGlass size={16} weight="bold" className="text-accent-primary" />
              Salary Research
            </h2>
            <div className="space-y-4">
              <Input
                label="Job Title"
                placeholder="e.g. Senior Software Engineer"
                value={jobTitle}
                onChange={(e) => setJobTitle(e.target.value)}
                icon={<CurrencyDollar size={16} weight="bold" />}
              />
              <Input
                label="Company (optional)"
                placeholder="e.g. Google"
                value={company}
                onChange={(e) => setCompany(e.target.value)}
                icon={<Building size={16} weight="bold" />}
              />
              <Input
                label="Location (optional)"
                placeholder="e.g. San Francisco, CA"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                icon={<MapPin size={16} weight="bold" />}
              />
              <Button
                variant="primary"
                loading={researchMutation.isPending}
                disabled={!jobTitle.trim()}
                onClick={() => researchMutation.mutate()}
                icon={<MagnifyingGlass size={14} weight="bold" />}
              >
                Research
              </Button>
            </div>
          </Card>

          {/* Research Results */}
          {researchMutation.isPending && (
            <Card>
              <Skeleton variant="text" className="w-1/2 h-5 mb-4" />
              <Skeleton variant="rect" className="w-full h-8 mb-4" />
              <div className="grid grid-cols-5 gap-2">
                {Array.from({ length: 5 }).map((_, i) => (
                  <div key={i} className="text-center space-y-1">
                    <Skeleton variant="text" className="w-full h-3" />
                    <Skeleton variant="text" className="w-full h-4" />
                  </div>
                ))}
              </div>
            </Card>
          )}

          {latestResearch && !researchMutation.isPending && (
            <Card>
              <h3 className="text-sm font-semibold text-text-primary mb-1 flex items-center gap-2">
                <TrendUp size={16} weight="bold" className="text-accent-success" />
                Salary Range
              </h3>
              {latestResearch.data_sources.length > 0 && (
                <p className="text-xs text-text-muted mb-4">
                  Based on {latestResearch.data_sources.length} sources ({latestResearch.currency})
                </p>
              )}
              <SalaryRangeBar research={latestResearch} />
            </Card>
          )}
        </div>

        {/* Right Column: Offer Evaluation */}
        <div className="space-y-6">
          <Card>
            <h2 className="text-sm font-semibold text-text-primary mb-4 flex items-center gap-2">
              <CurrencyDollar size={16} weight="bold" className="text-accent-success" />
              Offer Evaluation
            </h2>
            <div className="space-y-4">
              <p className="text-sm text-text-secondary">
                Enter an offer amount to see how it compares to market rates for the job title above.
              </p>
              <Input
                label="Offer Amount"
                type="number"
                placeholder="e.g. 150000"
                value={offerAmount}
                onChange={(e) => setOfferAmount(e.target.value)}
                icon={<CurrencyDollar size={16} weight="bold" />}
              />
              <Button
                variant="success"
                loading={evaluateMutation.isPending}
                disabled={!jobTitle.trim() || !offerAmount || Number(offerAmount) <= 0}
                onClick={() => evaluateMutation.mutate()}
                icon={<TrendUp size={14} weight="bold" />}
              >
                Evaluate Offer
              </Button>
            </div>
          </Card>

          {evaluateMutation.isPending && (
            <Card>
              <Skeleton variant="text" className="w-1/3 h-5 mb-3" />
              <Skeleton variant="text" className="w-full h-4 mb-2" />
              <Skeleton variant="text" className="w-2/3 h-4" />
            </Card>
          )}

          {evaluation && !evaluateMutation.isPending && (
            <Card>
              <h3 className="text-sm font-semibold text-text-primary mb-4">Evaluation Results</h3>
              <VerdictDisplay evaluation={evaluation} />
            </Card>
          )}

          {!evaluation && !evaluateMutation.isPending && (
            <div className="flex items-center justify-center py-12">
              <EmptyState
                icon={<CurrencyDollar size={40} weight="bold" />}
                title="No evaluation yet"
                description="Research a salary and enter an offer amount to evaluate"
              />
            </div>
          )}
        </div>
      </div>

      {/* Past Research */}
      {savedResearches.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-sm font-semibold text-text-primary flex items-center gap-2">
            <Clock size={16} weight="bold" className="text-text-muted" />
            Recent Research
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {savedResearches.map((saved) => (
              <Card key={saved.id} hover onClick={() => {
                setJobTitle(saved.job_title);
                setCompany(saved.company);
                setLocation(saved.location);
              }}>
                <div className="space-y-2">
                  <p className="text-sm font-medium text-text-primary truncate">
                    {saved.job_title}
                  </p>
                  <div className="flex items-center gap-2 text-xs text-text-muted">
                    {saved.company && (
                      <span className="flex items-center gap-1">
                        <Building size={10} weight="bold" />
                        {saved.company}
                      </span>
                    )}
                    {saved.location && (
                      <span className="flex items-center gap-1">
                        <MapPin size={10} weight="bold" />
                        {saved.location}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-semibold text-accent-primary">
                      {formatSalary(saved.research.median_salary ?? 0)}
                    </span>
                    <span className={cn('text-xs text-text-muted')}>
                      {formatSalary(saved.research.min_salary ?? 0)} - {formatSalary(saved.research.max_salary ?? 0)}
                    </span>
                  </div>
                  <p className="text-xs text-text-muted flex items-center gap-1">
                    <Clock size={10} weight="bold" />
                    {format(new Date(saved.timestamp), 'PP')}
                  </p>
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
