import {
  ArrowRight,
  Buildings,
  CheckCircle,
  Clock,
  Funnel,
  Kanban,
  Play,
  Sparkle,
} from "@phosphor-icons/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { formatDistanceToNow } from "date-fns";
import { motion } from "framer-motion";
import { useEffect, useState, type ReactNode } from "react";
import { pipelineApi, type Application } from "../api/pipeline";
import Button from "../components/ui/Button";
import { cn } from "../lib/utils";

const HERO_PANEL =
  "border-2 border-[var(--color-text-primary)] bg-bg-secondary shadow-[4px_4px_0px_0px_var(--color-text-primary)]";
const INSET_PANEL =
  "border-2 border-[var(--color-text-primary)] bg-bg-tertiary shadow-[4px_4px_0px_0px_var(--color-text-primary)]";
const CHIP =
  "inline-flex items-center gap-1 border-2 border-[var(--color-text-primary)] px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.18em]";
const BUTTON_BASE =
  "!rounded-none !border-2 !border-[var(--color-text-primary)] !uppercase !tracking-[0.18em] !shadow-[4px_4px_0px_0px_var(--color-text-primary)]";

const PIPELINE_STAGES = [
  { key: "saved", label: "Saved", tone: "bg-text-muted" },
  { key: "applied", label: "Applied", tone: "bg-accent-primary" },
  { key: "screening", label: "Screening", tone: "bg-accent-primary/70" },
  { key: "interviewing", label: "Interviewing", tone: "bg-accent-warning" },
  { key: "offer", label: "Offer", tone: "bg-accent-success" },
  { key: "accepted", label: "Accepted", tone: "bg-accent-success" },
] as const;

const NEXT_STAGE: Record<string, string | undefined> = {
  saved: "applied",
  applied: "screening",
  screening: "interviewing",
  interviewing: "offer",
  offer: "accepted",
};

function StageCard({
  application,
  selected,
  onSelect,
  onAdvance,
  isAdvancing,
}: {
  application: Application;
  selected: boolean;
  onSelect: () => void;
  onAdvance: () => void;
  isAdvancing: boolean;
}) {
  const nextStage = NEXT_STAGE[application.status];

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={onSelect}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          onSelect();
        }
      }}
      className={cn(
        "w-full border-2 border-[var(--color-text-primary)] p-4 text-left shadow-[4px_4px_0px_0px_var(--color-text-primary)] transition-transform duration-150 hover:-translate-x-1 hover:-translate-y-1",
        selected ? "bg-accent-primary/8" : "bg-bg-secondary"
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-text-muted">
            {application.status}
          </div>
          <h3 className="mt-2 truncate text-lg font-semibold tracking-[-0.05em] text-text-primary">
            {application.position_title ?? "Untitled application"}
          </h3>
          <div className="mt-2 flex items-center gap-1.5 text-xs text-text-secondary">
            <Buildings size={12} weight="bold" />
            <span className="truncate">{application.company_name ?? "Unknown company"}</span>
          </div>
        </div>
        <div className="flex shrink-0 flex-col items-end gap-2">
          <span className={CHIP}>{application.status}</span>
          {application.updated_at ? (
            <span className="text-[10px] uppercase tracking-[0.18em] text-text-muted">
              {formatDistanceToNow(new Date(application.updated_at), { addSuffix: true })}
            </span>
          ) : null}
        </div>
      </div>

      <div className="mt-4 flex items-center justify-between gap-3">
        <span className="text-xs text-text-muted">
          {application.source ?? "Unknown source"}
        </span>
        {nextStage ? (
          <Button
            variant="secondary"
            size="sm"
            onClick={(event) => {
              event.stopPropagation();
              onAdvance();
            }}
            loading={isAdvancing}
            icon={<ArrowRight size={14} weight="bold" />}
            className={cn(BUTTON_BASE, "bg-bg-secondary text-text-primary")}
          >
            Advance
          </Button>
        ) : (
          <span className={CHIP}>Final</span>
        )}
      </div>
    </div>
  );
}

function StageColumn({
  label,
  keyName,
  applications,
  selectedId,
  onSelect,
  onAdvance,
  advancingId,
}: {
  label: string;
  keyName: string;
  applications: Application[];
  selectedId: string | null;
  onSelect: (application: Application) => void;
  onAdvance: (application: Application) => void;
  advancingId: string | null;
}) {
  const tone = PIPELINE_STAGES.find((stage) => stage.key === keyName)?.tone ?? "bg-accent-primary";

  return (
    <div className="border-2 border-[var(--color-text-primary)] bg-bg-secondary shadow-[4px_4px_0px_0px_var(--color-text-primary)] xl:min-w-[18rem] xl:flex-[0_0_18rem]">
      <div className={cn("h-2 border-b-2 border-[var(--color-text-primary)]", tone)} />
      <div className="p-4">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <span className={cn("h-2.5 w-2.5 border border-[var(--color-text-primary)]", tone)} />
            <span className="text-sm font-semibold uppercase tracking-[-0.04em] text-text-primary">
              {label}
            </span>
          </div>
          <span className={CHIP}>{applications.length}</span>
        </div>

        <div className="mt-4 space-y-3">
          {applications.length ? (
            applications.map((application) => (
              <StageCard
                key={application.id}
                application={application}
                selected={selectedId === application.id}
                onSelect={() => onSelect(application)}
                onAdvance={() => onAdvance(application)}
                isAdvancing={advancingId === application.id}
              />
            ))
          ) : (
            <div className="border-2 border-dashed border-[var(--color-text-primary)] bg-bg-tertiary p-4">
              <p className="text-sm text-text-secondary">No applications in this stage.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function SummaryTile({
  label,
  value,
  hint,
  icon,
  tone,
}: {
  label: string;
  value: string;
  hint: string;
  icon: ReactNode;
  tone: string;
}) {
  return (
    <div className={cn("border-2 border-[var(--color-text-primary)] p-4 shadow-[4px_4px_0px_0px_var(--color-text-primary)]", tone)}>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-text-muted">
            {label}
          </div>
          <div className="mt-3 text-3xl font-semibold tracking-[-0.05em] text-text-primary">
            {value}
          </div>
          <p className="mt-2 text-sm leading-6 text-text-secondary">{hint}</p>
        </div>
        <div className="flex size-10 shrink-0 items-center justify-center border-2 border-[var(--color-text-primary)] bg-bg-secondary">
          {icon}
        </div>
      </div>
    </div>
  );
}

export default function Pipeline() {
  const queryClient = useQueryClient();
  const [selectedApplicationId, setSelectedApplicationId] = useState<string | null>(null);
  const [advancingId, setAdvancingId] = useState<string | null>(null);

  const { data: pipelineData, isLoading, isError } = useQuery({
    queryKey: ["pipeline"],
    queryFn: () => pipelineApi.pipeline().then((r) => r.data),
  });

  const stageColumns = PIPELINE_STAGES.map((stage) => ({
    ...stage,
    applications: pipelineData?.[stage.key] ?? [],
  }));

  const allApplications = stageColumns.flatMap((stage) => stage.applications);
  const selectedApplication = allApplications.find((application) => application.id === selectedApplicationId) ?? null;
  const firstApplicationId = allApplications[0]?.id ?? null;

  useEffect(() => {
    if (!selectedApplicationId && firstApplicationId) {
      setSelectedApplicationId(firstApplicationId);
    }
  }, [firstApplicationId, selectedApplicationId]);

  const transitionMutation = useMutation({
    mutationFn: async ({ application, nextStatus }: { application: Application; nextStatus: string }) => {
      setAdvancingId(application.id);
      return pipelineApi.transition(application.id, { new_status: nextStatus, note: `Moved to ${nextStatus}` });
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["pipeline"] });
      await queryClient.invalidateQueries({ queryKey: ["jobs"] });
    },
    onSettled: () => setAdvancingId(null),
  });

  const totalApplications = allApplications.length;
  const interviewAndBeyond = allApplications.filter((application) =>
    ["interviewing", "offer", "accepted"].includes(application.status)
  ).length;
  const followUpLoad = Math.max(totalApplications - interviewAndBeyond, 0);

  return (
    <div className="space-y-6 px-4 py-4 sm:px-6 sm:py-6">
      <motion.section
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
        className={cn(HERO_PANEL, "overflow-hidden")}
      >
        <div className="grid gap-0 xl:grid-cols-[minmax(0,1.4fr)_minmax(320px,0.8fr)]">
          <div className="p-5 sm:p-6 lg:p-8">
            <div className="flex flex-wrap items-center gap-2">
              <span className={CHIP}>Execute</span>
              <span className={CHIP}>{totalApplications.toLocaleString()} tracked</span>
              <span className={CHIP}>{interviewAndBeyond.toLocaleString()} late-stage</span>
            </div>
            <h1 className="mt-4 text-4xl font-semibold tracking-[-0.06em] sm:text-5xl lg:text-6xl">
              Pipeline
            </h1>
            <p className="mt-4 max-w-2xl text-sm leading-6 text-text-secondary sm:text-base">
              Track every application across the board, then promote a record with one click.
              The board becomes stacked and touch-friendly on smaller screens instead of hiding
              stage density behind a menu.
            </p>

            <div className="mt-6 flex flex-wrap gap-3">
              <Button
                variant="secondary"
                icon={<Funnel size={16} weight="bold" />}
                className={cn(BUTTON_BASE, "bg-bg-secondary text-text-primary")}
              >
                Filters
              </Button>
              <Button
                variant="secondary"
                icon={<Play size={16} weight="bold" />}
                className={cn(BUTTON_BASE, "bg-bg-secondary text-text-primary")}
              >
                Run auto-apply
              </Button>
              <Button
                variant="primary"
                icon={<Sparkle size={16} weight="bold" />}
                className={cn(BUTTON_BASE, "bg-accent-primary text-white")}
              >
                Open copilot
              </Button>
            </div>
          </div>

          <div className="border-t-2 border-[var(--color-text-primary)] bg-bg-tertiary p-5 sm:p-6 xl:border-l-2 xl:border-t-0">
            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
              <SummaryTile
                label="Board health"
                value={totalApplications.toLocaleString()}
                hint="Applications currently spread across the execution board."
                icon={<Kanban size={18} weight="bold" />}
                tone="bg-bg-secondary"
              />
              <SummaryTile
                label="Follow-up load"
                value={followUpLoad.toLocaleString()}
                hint="Items still needing a nudge or first response."
                icon={<Clock size={18} weight="bold" />}
                tone="bg-accent-warning/8"
              />
            </div>
          </div>
        </div>
      </motion.section>

      <section className="grid gap-4 md:grid-cols-3">
        <SummaryTile
          label="Board health"
          value={totalApplications.toLocaleString()}
          hint="Applications currently spread across the board."
          icon={<Kanban size={18} weight="bold" />}
          tone="bg-bg-secondary"
        />
        <SummaryTile
          label="Follow-up load"
          value={followUpLoad.toLocaleString()}
          hint="Items still needing a nudge or first response."
          icon={<Clock size={18} weight="bold" />}
          tone="bg-bg-secondary"
        />
        <SummaryTile
          label="Late-stage momentum"
          value={interviewAndBeyond.toLocaleString()}
          hint="Applications already in interviews, offers, or accepted."
          icon={<CheckCircle size={18} weight="bold" />}
          tone="bg-accent-success/8"
        />
      </section>

      <section className="grid gap-4 xl:grid-cols-[minmax(0,1.5fr)_minmax(360px,0.8fr)]">
        <div className={cn(HERO_PANEL, "overflow-hidden")}>
          <div className="border-b-2 border-[var(--color-text-primary)] bg-bg-tertiary px-5 py-4 sm:px-6">
            <div className="flex flex-wrap items-end justify-between gap-3">
              <div>
                <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-text-muted">
                  Board
                </div>
                <h2 className="mt-1 text-xl font-semibold uppercase tracking-[-0.04em] sm:text-2xl">
                  Stage columns
                </h2>
              </div>
              <span className={CHIP}>Touch friendly</span>
            </div>
          </div>

          <div className="p-4">
            {isLoading ? (
              <div className="grid gap-4 md:grid-cols-2 xl:flex xl:overflow-x-auto">
                {Array.from({ length: 6 }).map((_, index) => (
                  <div
                    key={index}
                    className="h-64 border-2 border-[var(--color-text-primary)] bg-bg-tertiary shadow-[4px_4px_0px_0px_var(--color-text-primary)] xl:min-w-[18rem] xl:flex-[0_0_18rem]"
                  />
                ))}
              </div>
            ) : isError ? (
              <div className="border-2 border-[var(--color-text-primary)] bg-accent-danger/10 p-5">
                <div className="text-sm font-semibold uppercase tracking-[0.18em] text-accent-danger">
                  Failed to load the pipeline
                </div>
                <p className="mt-2 text-sm leading-6 text-text-secondary">
                  Try again after the backend finishes responding.
                </p>
              </div>
            ) : (
              <div className="grid gap-4 md:grid-cols-2 xl:flex xl:overflow-x-auto">
                {stageColumns.map((stage) => (
                  <StageColumn
                    key={stage.key}
                    keyName={stage.key}
                    label={stage.label}
                    applications={stage.applications}
                    selectedId={selectedApplicationId}
                    onSelect={(application) => setSelectedApplicationId(application.id)}
                    onAdvance={(application) => {
                      const nextStatus = NEXT_STAGE[application.status];
                      if (!nextStatus) {
                        return;
                      }
                      transitionMutation.mutate({ application, nextStatus });
                    }}
                    advancingId={advancingId}
                  />
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="xl:sticky xl:top-6">
          <div className={cn(HERO_PANEL, "overflow-hidden")}>
            <div className="border-b-2 border-[var(--color-text-primary)] bg-bg-tertiary px-5 py-4 sm:px-6">
              <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-text-muted">
                Selected application
              </div>
              <h2 className="mt-1 text-xl font-semibold uppercase tracking-[-0.04em]">
                Detail sheet
              </h2>
            </div>

            {selectedApplication ? (
              <div className="space-y-4 p-5 sm:p-6">
                <div className="border-2 border-[var(--color-text-primary)] bg-bg-tertiary p-4">
                  <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-text-muted">
                    {selectedApplication.status}
                  </div>
                  <div className="mt-2 text-2xl font-semibold tracking-[-0.05em] text-text-primary">
                    {selectedApplication.position_title ?? "Untitled application"}
                  </div>
                  <div className="mt-2 flex items-center gap-1.5 text-sm text-text-secondary">
                    <Buildings size={14} weight="bold" />
                    {selectedApplication.company_name ?? "Unknown company"}
                  </div>
                </div>

                <div className="grid gap-3 sm:grid-cols-2">
                  <div className={cn(INSET_PANEL, "p-4")}>
                  <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-text-muted">
                    Source
                  </div>
                  <div className="mt-2 text-sm font-semibold uppercase tracking-[-0.03em] text-text-primary">
                      {selectedApplication.source
                        ? `Source • ${selectedApplication.source}`
                        : "Unknown"}
                  </div>
                </div>
                  <div className={cn(INSET_PANEL, "p-4")}>
                    <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-text-muted">
                      Salary
                    </div>
                    <div className="mt-2 text-sm font-semibold uppercase tracking-[-0.03em] text-text-primary">
                      {selectedApplication.salary_offered
                        ? `$${selectedApplication.salary_offered.toLocaleString()}`
                        : "Not recorded"}
                    </div>
                  </div>
                </div>

                <div className={cn(INSET_PANEL, "p-4")}>
                  <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-text-muted">
                    Notes
                  </div>
                  <p className="mt-2 text-sm leading-6 text-text-secondary">
                    {selectedApplication.notes ||
                      "No notes captured yet. Add context when you move the application forward."}
                  </p>
                </div>

                <div className="flex flex-wrap gap-2">
                  {NEXT_STAGE[selectedApplication.status] ? (
                    <Button
                      variant="primary"
                      loading={advancingId === selectedApplication.id}
                      onClick={() => {
                        const nextStatus = NEXT_STAGE[selectedApplication.status];
                        if (!nextStatus) {
                          return;
                        }
                        transitionMutation.mutate({ application: selectedApplication, nextStatus });
                      }}
                      icon={<ArrowRight size={16} weight="bold" />}
                      className={cn(BUTTON_BASE, "bg-accent-primary text-white")}
                    >
                      Advance
                    </Button>
                  ) : null}
                  <Button
                    variant="secondary"
                    onClick={() => setSelectedApplicationId(firstApplicationId)}
                    className={cn(BUTTON_BASE, "bg-bg-secondary text-text-primary")}
                  >
                    Reset selection
                  </Button>
                </div>
              </div>
            ) : (
              <div className="p-5 sm:p-6">
                <div className="border-2 border-[var(--color-text-primary)] bg-bg-tertiary p-5">
                  <div className="text-sm font-semibold uppercase tracking-[0.18em] text-text-muted">
                    Select an application
                  </div>
                  <p className="mt-3 text-sm leading-6 text-text-secondary">
                    Choose a record from the board to inspect its details and stage transition
                    actions.
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </section>
    </div>
  );
}
