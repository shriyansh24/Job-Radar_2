import { ArrowRight, Buildings, CheckCircle, Clock, Funnel, Kanban, Play, Sparkle } from "@phosphor-icons/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { formatDistanceToNow } from "date-fns";
import { useEffect, useMemo, useState } from "react";
import { pipelineApi, type Application } from "../api/pipeline";
import Badge from "../components/ui/Badge";
import Button from "../components/ui/Button";
import { PageHeader, SectionHeader, SplitWorkspace, StateBlock, Surface } from "../components/system";
import { cn } from "../lib/utils";

const PIPELINE_STAGES = [
  { key: "saved", label: "Saved", tone: "bg-text-muted" },
  { key: "applied", label: "Applied", tone: "bg-accent-primary" },
  { key: "screening", label: "Screening", tone: "bg-accent-primary/60" },
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

function ApplicationCard({
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
      className={[
        "w-full rounded-[var(--radius-lg)] border p-4 text-left transition-colors",
        selected
          ? "border-accent-primary/30 bg-accent-primary/8"
          : "border-border bg-bg-secondary hover:border-border/80 hover:bg-bg-hover",
      ].join(" ")}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="truncate text-sm font-semibold text-text-primary">
            {application.position_title ?? "Untitled application"}
          </div>
          <div className="mt-1 flex items-center gap-1.5 text-xs text-text-muted">
            <Buildings size={12} weight="bold" />
            <span className="truncate">{application.company_name ?? "Unknown company"}</span>
          </div>
        </div>
        <Badge size="sm" variant={application.status === "offer" || application.status === "accepted" ? "success" : "default"}>
          {application.status}
        </Badge>
      </div>

      <div className="mt-4 flex items-center justify-between gap-3">
        <div className="text-xs text-text-muted">
          {application.updated_at
            ? `Updated ${formatDistanceToNow(new Date(application.updated_at), { addSuffix: true })}`
            : "Recently updated"}
        </div>
        {nextStage ? (
          <Button
            variant="ghost"
            size="sm"
            onClick={(event) => {
              event.stopPropagation();
              onAdvance();
            }}
            loading={isAdvancing}
            icon={<ArrowRight size={14} weight="bold" />}
          >
            Advance
          </Button>
        ) : (
          <Badge size="sm" variant="success">
            Final
          </Badge>
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
  const stageTone = PIPELINE_STAGES.find((stage) => stage.key === keyName)?.tone ?? "bg-accent-primary";

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className={cn("h-2.5 w-2.5 rounded-full", stageTone)} />
          <span className="text-sm font-medium text-text-primary">{label}</span>
        </div>
        <span className="rounded-full border border-border bg-bg-secondary px-2 py-0.5 text-[11px] font-medium text-text-muted">
          {applications.length}
        </span>
      </div>

      <div className="space-y-2">
        {applications.length ? (
          applications.map((application) => (
            <ApplicationCard
              key={application.id}
              application={application}
              selected={selectedId === application.id}
              onSelect={() => onSelect(application)}
              onAdvance={() => onAdvance(application)}
              isAdvancing={advancingId === application.id}
            />
          ))
        ) : (
          <div className="rounded-[var(--radius-lg)] border border-dashed border-border/70 bg-bg-secondary/60 p-4">
            <p className="text-sm text-text-secondary">No applications in this stage.</p>
          </div>
        )}
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

  const stageColumns = useMemo(
    () =>
      PIPELINE_STAGES.map((stage) => ({
        ...stage,
        applications: pipelineData?.[stage.key] ?? [],
      })),
    [pipelineData]
  );

  const allApplications = useMemo(
    () => stageColumns.flatMap((stage) => stage.applications),
    [stageColumns]
  );

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

  return (
    <div className="space-y-6 px-4 py-4 sm:px-6 sm:py-6">
      <PageHeader
        eyebrow="Execute"
        title="Pipeline"
        description="Track every application across the board, then promote a record with one click."
        actions={
          <>
            <Button variant="secondary" icon={<Funnel size={16} weight="bold" />}>
              Filters
            </Button>
            <Button variant="secondary" icon={<Play size={16} weight="bold" />}>
              Run auto-apply
            </Button>
            <Button variant="primary" icon={<Sparkle size={16} weight="bold" />}>
              Open copilot
            </Button>
          </>
        }
        meta={
          <>
            <span>{totalApplications.toLocaleString()} tracked applications</span>
            <span>{interviewAndBeyond.toLocaleString()} in late-stage review</span>
          </>
        }
      />

      <Surface tone="default" radius="xl" padding="md">
        <div className="grid gap-4 md:grid-cols-3">
          <div className="rounded-[var(--radius-lg)] border border-border bg-bg-secondary p-4">
            <div className="flex items-center gap-2 text-xs uppercase tracking-[0.18em] text-text-muted">
              <Kanban size={14} weight="bold" />
              Board health
            </div>
            <div className="mt-3 text-2xl font-semibold tracking-[-0.04em] text-text-primary">
              {totalApplications.toLocaleString()}
            </div>
            <p className="mt-2 text-sm text-text-secondary">Applications currently spread across the execution board.</p>
          </div>
          <div className="rounded-[var(--radius-lg)] border border-border bg-bg-secondary p-4">
            <div className="flex items-center gap-2 text-xs uppercase tracking-[0.18em] text-text-muted">
              <Clock size={14} weight="bold" />
              Follow-up load
            </div>
            <div className="mt-3 text-2xl font-semibold tracking-[-0.04em] text-text-primary">
              {Math.max(totalApplications - interviewAndBeyond, 0).toLocaleString()}
            </div>
            <p className="mt-2 text-sm text-text-secondary">Items still needing a nudge or first response.</p>
          </div>
          <div className="rounded-[var(--radius-lg)] border border-border bg-bg-secondary p-4">
            <div className="flex items-center gap-2 text-xs uppercase tracking-[0.18em] text-text-muted">
              <CheckCircle size={14} weight="bold" />
              Late-stage momentum
            </div>
            <div className="mt-3 text-2xl font-semibold tracking-[-0.04em] text-text-primary">
              {interviewAndBeyond.toLocaleString()}
            </div>
            <p className="mt-2 text-sm text-text-secondary">Applications already in interviews, offers, or accepted.</p>
          </div>
        </div>
      </Surface>

      <SplitWorkspace
        primary={
          <Surface tone="default" radius="xl" padding="md">
            <SectionHeader
              title="Board"
              description="Advance a record from the stage cards or open one on the right for more detail."
            />

            <div className="mt-5 grid gap-4 xl:grid-cols-2 2xl:grid-cols-3">
              {isLoading ? (
                Array.from({ length: 6 }).map((_, index) => (
                  <div key={index} className="h-40 animate-pulse rounded-[var(--radius-lg)] bg-bg-hover/60" />
                ))
              ) : isError ? (
                <div className="xl:col-span-2 2xl:col-span-3">
                  <StateBlock
                    tone="danger"
                    title="Failed to load the pipeline"
                    description="Try again after the backend finishes responding."
                  />
                </div>
              ) : (
                stageColumns.map((stage) => (
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
                ))
              )}
            </div>
          </Surface>
        }
        secondary={
          <Surface tone="default" radius="xl" padding="md">
            <SectionHeader
              title="Selected application"
              description="Inspect the record that is currently selected in the board."
            />

            {selectedApplication ? (
              <div className="mt-5 space-y-4">
                <div>
                  <div className="text-[11px] font-medium uppercase tracking-[0.18em] text-text-muted">
                    {selectedApplication.status}
                  </div>
                  <div className="mt-1 text-xl font-semibold tracking-[-0.04em] text-text-primary">
                    {selectedApplication.position_title ?? "Untitled application"}
                  </div>
                  <div className="mt-1 flex items-center gap-1.5 text-sm text-text-secondary">
                    <Buildings size={14} weight="bold" />
                    {selectedApplication.company_name ?? "Unknown company"}
                  </div>
                </div>

                <div className="grid gap-3 sm:grid-cols-2">
                  <div className="rounded-[var(--radius-lg)] border border-border bg-bg-secondary p-4">
                    <div className="text-xs uppercase tracking-[0.18em] text-text-muted">Source</div>
                    <div className="mt-2 text-sm font-medium text-text-primary">
                      {selectedApplication.source ?? "Unknown"}
                    </div>
                  </div>
                  <div className="rounded-[var(--radius-lg)] border border-border bg-bg-secondary p-4">
                    <div className="text-xs uppercase tracking-[0.18em] text-text-muted">Salary</div>
                    <div className="mt-2 text-sm font-medium text-text-primary">
                      {selectedApplication.salary_offered ? `$${selectedApplication.salary_offered.toLocaleString()}` : "Not recorded"}
                    </div>
                  </div>
                </div>

                <div className="rounded-[var(--radius-lg)] border border-border bg-bg-secondary p-4">
                  <div className="text-xs uppercase tracking-[0.18em] text-text-muted">Notes</div>
                  <p className="mt-2 text-sm leading-6 text-text-secondary">
                    {selectedApplication.notes || "No notes captured yet. Add context when you move the application forward."}
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
                    >
                      Advance
                    </Button>
                  ) : null}
                  <Button variant="secondary" onClick={() => setSelectedApplicationId(firstApplicationId)}>
                    Reset selection
                  </Button>
                </div>
              </div>
            ) : (
              <div className="mt-5">
                <StateBlock
                  tone="neutral"
                  title="Select an application"
                  description="Choose a record from the board to inspect its details and stage transition actions."
                />
              </div>
            )}
          </Surface>
        }
      />
    </div>
  );
}
