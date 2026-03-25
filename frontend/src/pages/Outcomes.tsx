import {
  ArrowUpRight,
  Briefcase,
  Buildings,
  ChartBar,
  CheckCircle,
  Ghost,
  HandCoins,
  TrendUp,
} from "@phosphor-icons/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AxiosError } from "axios";
import { formatDistanceToNow } from "date-fns";
import { motion } from "framer-motion";
import { useEffect, useState } from "react";
import { outcomesApi, type CompanyInsight, type OutcomeMutation } from "../api/outcomes";
import { pipelineApi } from "../api/pipeline";
import Badge from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import EmptyState from "../components/ui/EmptyState";
import Input from "../components/ui/Input";
import Select from "../components/ui/Select";
import Skeleton from "../components/ui/Skeleton";
import Textarea from "../components/ui/Textarea";
import { toast } from "../components/ui/toastService";
import { cn } from "../lib/utils";

const HERO_PANEL =
  "border-2 border-[var(--color-text-primary)] bg-bg-secondary shadow-[4px_4px_0px_0px_var(--color-text-primary)]";
const INSET_PANEL =
  "border-2 border-[var(--color-text-primary)] bg-bg-tertiary shadow-[4px_4px_0px_0px_var(--color-text-primary)]";
const CHIP =
  "inline-flex items-center gap-1 border-2 border-[var(--color-text-primary)] px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.18em]";
const BUTTON_BASE =
  "!rounded-none !border-2 !border-[var(--color-text-primary)] !uppercase !tracking-[0.18em] !shadow-[4px_4px_0px_0px_var(--color-text-primary)]";

const STAGE_OPTIONS = [
  { value: "", label: "Not specified" },
  { value: "applied", label: "Applied" },
  { value: "screening", label: "Screening" },
  { value: "interview", label: "Interview" },
  { value: "final_round", label: "Final round" },
  { value: "offer", label: "Offer" },
];

const DECISION_OPTIONS = [
  { value: "", label: "Not specified" },
  { value: "accepted", label: "Accepted" },
  { value: "declined", label: "Declined" },
  { value: "rejected", label: "Rejected" },
  { value: "withdrawn", label: "Withdrawn" },
];

const METHOD_OPTIONS = [
  { value: "", label: "Not specified" },
  { value: "direct", label: "Direct" },
  { value: "job_board", label: "Job board" },
  { value: "recruiter", label: "Recruiter" },
  { value: "referral", label: "Referral" },
];

const emptyForm: OutcomeMutation = {
  stage_reached: null,
  rejection_reason: null,
  rejection_stage: null,
  days_to_response: null,
  offer_amount: null,
  offer_equity: null,
  offer_total_comp: null,
  negotiated_amount: null,
  final_decision: null,
  was_ghosted: false,
  referral_used: false,
  cover_letter_used: false,
  application_method: null,
  feedback_notes: null,
};

function SummaryTile({
  icon,
  label,
  value,
  hint,
  tone = "default",
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  hint: string;
  tone?: "default" | "primary" | "success" | "warning";
}) {
  const toneClass = {
    default: "bg-bg-secondary",
    primary: "bg-accent-primary/8",
    success: "bg-accent-success/8",
    warning: "bg-accent-warning/8",
  }[tone];

  return (
    <div className={cn(HERO_PANEL, "p-4", toneClass)}>
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-text-muted">
            {label}
          </div>
          <div className="mt-3 text-3xl font-semibold tracking-[-0.05em] text-text-primary">
            {value}
          </div>
          <p className="mt-2 text-sm leading-6 text-text-secondary">{hint}</p>
        </div>
        <div className="flex size-11 shrink-0 items-center justify-center border-2 border-[var(--color-text-primary)] bg-bg-tertiary">
          {icon}
        </div>
      </div>
    </div>
  );
}

function ToggleChip({
  active,
  label,
  onClick,
}: {
  active: boolean;
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "border-2 px-3 py-2 text-[11px] font-semibold uppercase tracking-[0.18em] transition-colors duration-[var(--transition-fast)]",
        active
          ? "border-[var(--color-text-primary)] bg-accent-primary text-white"
          : "border-[var(--color-text-primary)] bg-bg-secondary text-text-secondary hover:bg-bg-tertiary hover:text-text-primary"
      )}
    >
      {label}
    </button>
  );
}

function CompanyMetric({
  label,
  value,
  hint,
}: {
  label: string;
  value: string;
  hint: string;
}) {
  return (
    <div className={cn(HERO_PANEL, "p-4")}>
      <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-text-muted">
        {label}
      </div>
      <div className="mt-2 text-2xl font-semibold tracking-[-0.05em] text-text-primary">{value}</div>
      <p className="mt-2 text-sm leading-6 text-text-secondary">{hint}</p>
    </div>
  );
}

export default function Outcomes() {
  const queryClient = useQueryClient();
  const [selectedApplicationId, setSelectedApplicationId] = useState("");
  const [companyQuery, setCompanyQuery] = useState("");
  const [companyInsight, setCompanyInsight] = useState<CompanyInsight | null>(null);
  const [form, setForm] = useState<OutcomeMutation>({ ...emptyForm });

  const { data: stats, isLoading: loadingStats } = useQuery({
    queryKey: ["outcomes", "stats"],
    queryFn: () => outcomesApi.getStats().then((response) => response.data),
  });

  const { data: applications } = useQuery({
    queryKey: ["applications", "outcomes-context"],
    queryFn: () => pipelineApi.list(1, 24).then((response) => response.data),
  });

  useEffect(() => {
    if (!selectedApplicationId && applications?.items.length) {
      const first = applications.items[0];
      setSelectedApplicationId(first.id);
      setCompanyQuery(first.company_name ?? "");
    }
  }, [applications, selectedApplicationId]);

  const outcomeQuery = useQuery({
    queryKey: ["outcomes", selectedApplicationId],
    queryFn: () => outcomesApi.get(selectedApplicationId).then((response) => response.data),
    enabled: Boolean(selectedApplicationId),
    retry: false,
  });

  useEffect(() => {
    if (outcomeQuery.data) {
      setForm({
        stage_reached: outcomeQuery.data.stage_reached,
        rejection_reason: outcomeQuery.data.rejection_reason,
        rejection_stage: outcomeQuery.data.rejection_stage,
        days_to_response: outcomeQuery.data.days_to_response,
        offer_amount: outcomeQuery.data.offer_amount,
        offer_equity: outcomeQuery.data.offer_equity,
        offer_total_comp: outcomeQuery.data.offer_total_comp,
        negotiated_amount: outcomeQuery.data.negotiated_amount,
        final_decision: outcomeQuery.data.final_decision,
        was_ghosted: outcomeQuery.data.was_ghosted,
        referral_used: outcomeQuery.data.referral_used,
        cover_letter_used: outcomeQuery.data.cover_letter_used,
        application_method: outcomeQuery.data.application_method,
        feedback_notes: outcomeQuery.data.feedback_notes,
      });
      return;
    }

    const error = outcomeQuery.error as AxiosError | null;
    if (error?.response?.status === 404) {
      setForm({ ...emptyForm });
    }
  }, [outcomeQuery.data, outcomeQuery.error]);

  const companyInsightMutation = useMutation({
    mutationFn: (company: string) => outcomesApi.getCompanyInsights(company).then((response) => response.data),
    onSuccess: (insight) => setCompanyInsight(insight),
    onError: () => toast("error", "Failed to load company insights"),
  });

  const saveMutation = useMutation({
    mutationFn: () => {
      if (!selectedApplicationId) {
        throw new Error("Application is required");
      }

      const error = outcomeQuery.error as AxiosError | null;
      const isMissing = error?.response?.status === 404 || !outcomeQuery.data;
      if (isMissing) {
        return outcomesApi.create(selectedApplicationId, form).then((response) => response.data);
      }
      return outcomesApi.update(selectedApplicationId, form).then((response) => response.data);
    },
    onSuccess: () => {
      toast("success", "Outcome saved");
      queryClient.invalidateQueries({ queryKey: ["outcomes", selectedApplicationId] });
      queryClient.invalidateQueries({ queryKey: ["outcomes", "stats"] });
    },
    onError: () => toast("error", "Failed to save outcome"),
  });

  const selectedApplication =
    applications?.items.find((application) => application.id === selectedApplicationId) ?? null;
  const applicationOptions =
    applications?.items.map((application) => ({
      value: application.id,
      label: `${application.position_title ?? "Unknown role"} • ${application.company_name ?? "Unknown company"}`,
    })) ?? [];

  const rejectionTotal =
    stats?.top_rejection_reasons.reduce((sum, item) => sum + item.count, 0) ?? 0;

  return (
    <div className="space-y-6 px-4 py-4 sm:px-6 sm:py-6">
      <motion.section
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
        className={cn(HERO_PANEL, "overflow-hidden")}
      >
        <div className="grid gap-0 xl:grid-cols-[minmax(0,1.25fr)_minmax(320px,0.95fr)]">
          <div className="p-5 sm:p-6 lg:p-8">
            <div className="flex flex-wrap items-center gap-2">
              <span className={CHIP}>Intelligence</span>
              <span className={CHIP}>Application outcomes</span>
              <span className={CHIP}>Company patterns</span>
            </div>
            <h1 className="mt-4 text-4xl font-semibold tracking-[-0.06em] sm:text-5xl lg:text-6xl">
              Outcomes
            </h1>
            <p className="mt-4 max-w-2xl text-sm leading-6 text-text-secondary sm:text-base">
              Track what happened after applications, compare company patterns, and keep the career
              data grounded in real history.
            </p>
          </div>

          <div className="border-t-2 border-[var(--color-text-primary)] bg-bg-tertiary p-5 sm:p-6 xl:border-l-2 xl:border-t-0">
            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
              <SummaryTile
                icon={<TrendUp size={18} weight="bold" className="text-accent-primary" />}
                label="Response Rate"
                value={loadingStats ? "..." : `${Math.round((stats?.response_rate ?? 0) * 100)}%`}
                hint="Applications that led to an actual response."
                tone="primary"
              />
              <SummaryTile
                icon={<Ghost size={18} weight="bold" className="text-accent-warning" />}
                label="Ghost Rate"
                value={loadingStats ? "..." : `${Math.round((stats?.ghosting_rate ?? 0) * 100)}%`}
                hint="Applications that never received a meaningful reply."
                tone="warning"
              />
              <SummaryTile
                icon={<HandCoins size={18} weight="bold" className="text-accent-success" />}
                label="Avg Offer"
                value={
                  loadingStats
                    ? "..."
                    : stats?.avg_offer_amount
                      ? `$${Math.round(stats.avg_offer_amount).toLocaleString()}`
                      : "$0"
                }
                hint="Average offer amount where compensation was captured."
                tone="success"
              />
            </div>
          </div>
        </div>
      </motion.section>

      <section className="grid gap-4 xl:grid-cols-[minmax(0,1.25fr)_minmax(360px,0.95fr)]">
        <div className="space-y-4">
          <div className={cn(HERO_PANEL, "p-5 sm:p-6")}>
            <div className="flex items-start justify-between gap-4">
              <div>
                <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-text-muted">
                  Capture
                </div>
                <h2 className="mt-2 text-xl font-semibold uppercase tracking-[-0.04em] text-text-primary">
                  Outcome capture
                </h2>
                <p className="mt-3 text-sm leading-6 text-text-secondary">
                  Record the stage, decision, and notes while the sequence is still fresh.
                </p>
              </div>
              <div className="flex size-11 shrink-0 items-center justify-center border-2 border-[var(--color-text-primary)] bg-bg-tertiary">
                <Briefcase size={18} weight="bold" className="text-accent-primary" />
              </div>
            </div>

            <div className="mt-5 grid gap-4 border-t-2 border-[var(--color-text-primary)] pt-5 md:grid-cols-2">
              <Select
                label="Application"
                value={selectedApplicationId}
                onChange={(event) => {
                  const nextId = event.target.value;
                  setSelectedApplicationId(nextId);
                  const nextApplication = applications?.items.find((application) => application.id === nextId);
                  setCompanyQuery(nextApplication?.company_name ?? "");
                }}
                options={applicationOptions}
                placeholder="Choose an application"
              />
              <Select
                label="Stage reached"
                value={form.stage_reached ?? ""}
                onChange={(event) =>
                  setForm((current) => ({ ...current, stage_reached: event.target.value || null }))
                }
                options={STAGE_OPTIONS}
              />
              <Select
                label="Final decision"
                value={form.final_decision ?? ""}
                onChange={(event) =>
                  setForm((current) => ({ ...current, final_decision: event.target.value || null }))
                }
                options={DECISION_OPTIONS}
              />
              <Select
                label="Application method"
                value={form.application_method ?? ""}
                onChange={(event) =>
                  setForm((current) => ({ ...current, application_method: event.target.value || null }))
                }
                options={METHOD_OPTIONS}
              />
              <Input
                label="Days to response"
                type="number"
                value={form.days_to_response?.toString() ?? ""}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    days_to_response: event.target.value ? Number(event.target.value) : null,
                  }))
                }
                placeholder="e.g. 6"
              />
              <Input
                label="Offer total comp"
                type="number"
                value={form.offer_total_comp?.toString() ?? ""}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    offer_total_comp: event.target.value ? Number(event.target.value) : null,
                  }))
                }
                placeholder="e.g. 240000"
              />
              <Input
                label="Rejection reason"
                value={form.rejection_reason ?? ""}
                onChange={(event) =>
                  setForm((current) => ({ ...current, rejection_reason: event.target.value || null }))
                }
                placeholder="e.g. Experience depth"
              />
              <Input
                label="Rejection stage"
                value={form.rejection_stage ?? ""}
                onChange={(event) =>
                  setForm((current) => ({ ...current, rejection_stage: event.target.value || null }))
                }
                placeholder="e.g. Hiring manager screen"
              />
            </div>

            <div className="mt-4 flex flex-wrap gap-2">
              <ToggleChip
                active={Boolean(form.was_ghosted)}
                label="Ghosted"
                onClick={() => setForm((current) => ({ ...current, was_ghosted: !current.was_ghosted }))}
              />
              <ToggleChip
                active={Boolean(form.referral_used)}
                label="Referral used"
                onClick={() => setForm((current) => ({ ...current, referral_used: !current.referral_used }))}
              />
              <ToggleChip
                active={Boolean(form.cover_letter_used)}
                label="Cover letter used"
                onClick={() =>
                  setForm((current) => ({ ...current, cover_letter_used: !current.cover_letter_used }))
                }
              />
            </div>

            <div className="mt-4">
              <Textarea
                label="Feedback notes"
                className="min-h-[180px]"
                value={form.feedback_notes ?? ""}
                onChange={(event) =>
                  setForm((current) => ({ ...current, feedback_notes: event.target.value || null }))
                }
                placeholder="Capture recruiter comments, interview notes, friction, or the reason this outcome matters."
              />
            </div>

            <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t-2 border-[var(--color-text-primary)] pt-4">
              <div className="text-sm text-text-secondary">
                {selectedApplication ? (
                  <>
                    Tracking <span className="font-medium text-text-primary">{selectedApplication.position_title ?? "Unknown role"}</span>
                    {" at "}
                    <span className="font-medium text-text-primary">{selectedApplication.company_name ?? "Unknown company"}</span>
                  </>
                ) : (
                  "Choose an application to record an outcome."
                )}
              </div>
              <Button
                variant="default"
                onClick={() => saveMutation.mutate()}
                disabled={!selectedApplicationId}
                className={cn(BUTTON_BASE, "bg-accent-primary text-white")}
              >
                <CheckCircle size={16} weight="bold" />
                Save outcome
              </Button>
            </div>
          </div>

          <div className={cn(HERO_PANEL, "overflow-hidden")}>
            <div className="border-b-2 border-[var(--color-text-primary)] bg-bg-tertiary px-5 py-4 sm:px-6">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-text-muted">
                    Intelligence
                  </div>
                  <div className="mt-1 text-xl font-semibold uppercase tracking-[-0.04em] text-text-primary">
                    Outcome intelligence
                  </div>
                </div>
                <span className={CHIP}>Live analysis</span>
              </div>
            </div>

            <div className="p-5 sm:p-6">
              {loadingStats ? (
                <div className="space-y-3">
                  <Skeleton variant="rect" className="h-24 w-full" />
                  <Skeleton variant="rect" className="h-24 w-full" />
                </div>
              ) : (
                <div className="grid gap-6 lg:grid-cols-2">
                  <div>
                    <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-text-muted">
                      Stage distribution
                    </div>
                    <div className="mt-4 space-y-3">
                      {Object.entries(stats?.stage_distribution ?? {}).length ? (
                        Object.entries(stats?.stage_distribution ?? {}).map(([stage, count]) => {
                          const max = Math.max(...Object.values(stats?.stage_distribution ?? { fallback: 1 }));
                          const width = max ? `${(count / max) * 100}%` : "0%";
                          return (
                            <div key={stage} className="space-y-1.5">
                              <div className="flex items-center justify-between gap-3 text-sm">
                                <span className="capitalize text-text-secondary">{stage.replace(/_/g, " ")}</span>
                                <span className="font-semibold text-text-primary">{count}</span>
                              </div>
                              <div className="h-4 border-2 border-[var(--color-text-primary)] bg-bg-secondary">
                                <div className="h-full bg-accent-primary" style={{ width }} />
                              </div>
                            </div>
                          );
                        })
                      ) : (
                        <EmptyState
                          icon={<ChartBar size={28} weight="bold" />}
                          title="No stage distribution yet"
                          description="Save outcomes to build a funnel view grounded in real application history."
                          className="bg-bg-tertiary"
                        />
                      )}
                    </div>
                  </div>

                  <div>
                    <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-text-muted">
                      Top rejection reasons
                    </div>
                    <div className="mt-4 space-y-3">
                      {stats?.top_rejection_reasons.length ? (
                        stats.top_rejection_reasons.map((item) => (
                          <div key={item.reason} className={cn(HERO_PANEL, "p-4")}>
                            <div className="flex items-center justify-between gap-3">
                              <div className="text-sm text-text-primary">{item.reason}</div>
                              <Badge variant="warning" className="border-[var(--color-text-primary)]">
                                {item.count}
                              </Badge>
                            </div>
                            <div className="mt-2 text-xs text-text-muted">
                              {rejectionTotal ? Math.round((item.count / rejectionTotal) * 100) : 0}% of tracked rejections
                            </div>
                          </div>
                        ))
                      ) : (
                        <EmptyState
                          icon={<ArrowUpRight size={28} weight="bold" />}
                          title="No rejection reasons yet"
                          description="Structured rejections will show up here once you record them."
                          className="bg-bg-tertiary"
                        />
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <div className={cn(HERO_PANEL, "overflow-hidden")}>
            <div className="border-b-2 border-[var(--color-text-primary)] bg-bg-tertiary px-5 py-4 sm:px-6">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-text-muted">
                    Lookup
                  </div>
                  <div className="mt-1 text-xl font-semibold uppercase tracking-[-0.04em] text-text-primary">
                    Company insight lookup
                  </div>
                </div>
                <span className={CHIP}>Single target view</span>
              </div>
            </div>

            <div className="p-5 sm:p-6">
              <p className="text-sm leading-6 text-text-secondary">
                Pull a single-company view to see whether the pattern is you, the company, or the stage.
              </p>
              <div className="mt-4 flex flex-col gap-3 sm:flex-row">
                <Input
                  value={companyQuery}
                  onChange={(event) => setCompanyQuery(event.target.value)}
                  placeholder="Search a company"
                  icon={<Buildings size={16} weight="bold" />}
                />
                <Button
                  variant="secondary"
                  onClick={() => companyInsightMutation.mutate(companyQuery)}
                  disabled={!companyQuery.trim() || companyInsightMutation.isPending}
                  className={cn(BUTTON_BASE, "bg-bg-secondary text-text-primary")}
                >
                  <TrendUp size={16} weight="bold" />
                  Lookup
                </Button>
              </div>

              <div className="mt-5 border-t-2 border-[var(--color-text-primary)] pt-5">
                {companyInsightMutation.isPending ? (
                  <div className="space-y-3">
                    <Skeleton variant="rect" className="h-24 w-full" />
                    <Skeleton variant="rect" className="h-20 w-full" />
                    <Skeleton variant="rect" className="h-20 w-full" />
                  </div>
                ) : companyInsight ? (
                  <div className="space-y-4">
                    <div className={cn(HERO_PANEL, "p-4 bg-accent-primary/8")}>
                      <div className="text-lg font-semibold tracking-[-0.04em] text-text-primary">
                        {companyInsight.company_name}
                      </div>
                      <p className="mt-1 text-sm text-text-secondary">
                        {companyInsight.total_applications} applications tracked across this company.
                      </p>
                    </div>

                    <div className="grid gap-3 sm:grid-cols-2">
                      <CompanyMetric
                        label="Callback Rate"
                        value={`${Math.round((companyInsight.callback_count / Math.max(companyInsight.total_applications, 1)) * 100)}%`}
                        hint="Callbacks relative to total applications."
                      />
                      <CompanyMetric
                        label="Ghost Rate"
                        value={`${Math.round(companyInsight.ghost_rate * 100)}%`}
                        hint="How often the process went silent."
                      />
                      <CompanyMetric
                        label="Offer Rate"
                        value={`${Math.round(companyInsight.offer_rate * 100)}%`}
                        hint="Offer conversion for this company."
                      />
                      <CompanyMetric
                        label="Avg Response"
                        value={
                          companyInsight.avg_response_days !== null
                            ? `${companyInsight.avg_response_days.toFixed(1)}d`
                            : "N/A"
                        }
                        hint="Average days to a response."
                      />
                    </div>

                    {companyInsight.culture_notes ? (
                      <div className={cn(INSET_PANEL, "p-4 text-sm leading-6 text-text-secondary")}>
                        {companyInsight.culture_notes}
                      </div>
                    ) : null}
                    {companyInsight.last_applied_at ? (
                      <div className="text-xs text-text-muted">
                        Last applied {formatDistanceToNow(new Date(companyInsight.last_applied_at), { addSuffix: true })}
                      </div>
                    ) : null}
                  </div>
                ) : (
                  <EmptyState
                    icon={<Buildings size={30} weight="bold" />}
                    title="No company insight selected"
                    description="Run a lookup to see company-level response patterns and notes."
                    className="bg-bg-tertiary"
                  />
                )}
              </div>
            </div>
          </div>

          <div className={cn(INSET_PANEL, "p-5 sm:p-6")}>
            <div className="flex items-center gap-2 text-sm font-semibold uppercase tracking-[0.18em] text-text-muted">
              <Buildings size={16} weight="bold" />
              Reading this page
            </div>
            <div className="mt-3 space-y-2 text-sm leading-6 text-text-secondary">
              <p>Outcomes are tied to applications, not raw jobs, so the surface respects the hiring journey.</p>
              <p>Capture even partial feedback. Structured fragments are more useful than perfect memory.</p>
              <p>Use company lookup when you suspect a repeated failure mode with one target employer.</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
