import { ArrowUpRight, ChartBar, CheckCircle } from "@phosphor-icons/react";
import type { Dispatch, SetStateAction } from "react";
import type { OutcomeMutation } from "../../api/outcomes";
import Badge from "../ui/Badge";
import { Button } from "../ui/Button";
import EmptyState from "../ui/EmptyState";
import Input from "../ui/Input";
import Select from "../ui/Select";
import Skeleton from "../ui/Skeleton";
import Textarea from "../ui/Textarea";
import { SectionHeader } from "../system/SectionHeader";
import { Surface } from "../system/Surface";
import { ToggleChip } from "./ToggleChip";

type OutcomeStats = {
  response_rate: number;
  ghosting_rate: number;
  avg_offer_amount: number | null;
  stage_distribution?: Record<string, number>;
  top_rejection_reasons?: Array<{ reason: string; count: number }>;
};

export function OutcomeCapturePanel({
  applications,
  applicationOptions,
  selectedApplicationId,
  setSelectedApplicationId,
  setCompanyQuery,
  form,
  setForm,
  selectedApplication,
  saveMutation,
  stats,
  loadingStats,
  rejectionTotal,
}: {
  applications: Array<{ id: string; company_name?: string | null; position_title?: string | null }> | undefined;
  applicationOptions: Array<{ value: string; label: string }>;
  selectedApplicationId: string;
  setSelectedApplicationId: (value: string) => void;
  setCompanyQuery: (value: string) => void;
  form: OutcomeMutation;
  setForm: Dispatch<SetStateAction<OutcomeMutation>>;
  selectedApplication: { position_title?: string | null; company_name?: string | null } | null;
  saveMutation: { mutate: () => void; isPending: boolean };
  stats: OutcomeStats | undefined;
  loadingStats: boolean;
  rejectionTotal: number;
}) {
  const stageOptions = [
    { value: "", label: "Not specified" },
    { value: "applied", label: "Applied" },
    { value: "screening", label: "Screening" },
    { value: "interview", label: "Interview" },
    { value: "final_round", label: "Final round" },
    { value: "offer", label: "Offer" },
  ];

  const decisionOptions = [
    { value: "", label: "Not specified" },
    { value: "accepted", label: "Accepted" },
    { value: "declined", label: "Declined" },
    { value: "rejected", label: "Rejected" },
    { value: "withdrawn", label: "Withdrawn" },
  ];

  const methodOptions = [
    { value: "", label: "Not specified" },
    { value: "direct", label: "Direct" },
    { value: "job_board", label: "Job board" },
    { value: "recruiter", label: "Recruiter" },
    { value: "referral", label: "Referral" },
  ];

  return (
    <div className="space-y-4">
      <Surface tone="default" padding="lg" radius="xl">
        <SectionHeader
          title="Outcome capture"
          description="Record the stage, decision, and notes while the sequence is still fresh."
        />

        <div className="mt-5 grid gap-4 md:grid-cols-2">
          <Select
            label="Application"
            value={selectedApplicationId}
            onChange={(event) => {
              const nextId = event.target.value;
              setSelectedApplicationId(nextId);
              const nextApplication = applications?.find((application) => application.id === nextId);
              setCompanyQuery(nextApplication?.company_name ?? "");
            }}
            options={applicationOptions}
            placeholder="Choose an application"
          />
          <Select
            label="Stage reached"
            value={form.stage_reached ?? ""}
            onChange={(event) => setForm((current) => ({ ...current, stage_reached: event.target.value || null }))}
            options={stageOptions}
          />
          <Select
            label="Final decision"
            value={form.final_decision ?? ""}
            onChange={(event) => setForm((current) => ({ ...current, final_decision: event.target.value || null }))}
            options={decisionOptions}
          />
          <Select
            label="Application method"
            value={form.application_method ?? ""}
            onChange={(event) =>
              setForm((current) => ({ ...current, application_method: event.target.value || null }))
            }
            options={methodOptions}
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
            onChange={(event) => setForm((current) => ({ ...current, rejection_reason: event.target.value || null }))}
            placeholder="e.g. Experience depth"
          />
          <Input
            label="Rejection stage"
            value={form.rejection_stage ?? ""}
            onChange={(event) => setForm((current) => ({ ...current, rejection_stage: event.target.value || null }))}
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
            onClick={() => setForm((current) => ({ ...current, cover_letter_used: !current.cover_letter_used }))}
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

        <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t-2 border-border pt-4">
          <div className="text-sm text-text-secondary">
            {selectedApplication ? (
              <>
                Tracking{" "}
                <span className="font-medium text-text-primary">
                  {selectedApplication.position_title ?? "Unknown role"}
                </span>
                {" at "}
                <span className="font-medium text-text-primary">
                  {selectedApplication.company_name ?? "Unknown company"}
                </span>
              </>
            ) : (
              "Choose an application to record an outcome."
            )}
          </div>
          <Button
            variant="primary"
            onClick={() => saveMutation.mutate()}
            disabled={!selectedApplicationId}
            icon={<CheckCircle size={16} weight="bold" />}
          >
            Save outcome
          </Button>
        </div>
      </Surface>

      <Surface tone="subtle" padding="lg" radius="xl">
        <SectionHeader
          title="Outcome intelligence"
          description="Stage distribution and rejection reasons stay on the same surface so the feedback loop is easy to scan."
          action={<Badge variant="info">Live analysis</Badge>}
        />

        <div className="mt-5 grid gap-6 lg:grid-cols-2">
          {loadingStats ? (
            <div className="space-y-3">
              <Skeleton variant="rect" className="h-24 w-full" />
              <Skeleton variant="rect" className="h-24 w-full" />
            </div>
          ) : (
            <div>
              <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
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
                        <div className="h-4 border-2 border-border bg-[var(--color-bg-secondary)]">
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
                  />
                )}
              </div>
            </div>
          )}

          <div>
            <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
              Top rejection reasons
            </div>
            <div className="mt-4 space-y-3">
              {stats?.top_rejection_reasons?.length ? (
                stats.top_rejection_reasons.map((item) => (
                  <Surface key={item.reason} tone="default" padding="md" radius="xl">
                    <div className="flex items-center justify-between gap-3">
                      <div className="text-sm text-text-primary">{item.reason}</div>
                      <Badge variant="warning" className="border-[var(--color-text-primary)]">
                        {item.count}
                      </Badge>
                    </div>
                    <div className="mt-2 text-xs text-muted-foreground">
                      {rejectionTotal ? Math.round((item.count / rejectionTotal) * 100) : 0}% of tracked rejections
                    </div>
                  </Surface>
                ))
              ) : (
                <EmptyState
                  icon={<ArrowUpRight size={28} weight="bold" />}
                  title="No rejection reasons yet"
                  description="Structured rejections will show up here once you record them."
                />
              )}
            </div>
          </div>
        </div>
      </Surface>
    </div>
  );
}
