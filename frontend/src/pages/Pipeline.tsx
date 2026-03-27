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
import { useEffect, useState } from "react";
import { pipelineApi, type Application } from "../api/pipeline";
import Badge from "../components/ui/Badge";
import Button from "../components/ui/Button";
import {
  MetricStrip,
  PageHeader,
  SplitWorkspace,
  StateBlock,
  Surface,
} from "../components/system";
import { cn } from "../lib/utils";

const PIPELINE_STAGES = [
  { key: "saved", label: "Saved", tone: "bg-[var(--color-text-muted)]" },
  { key: "applied", label: "Applied", tone: "bg-[var(--color-accent-primary)]" },
  { key: "screening", label: "Screening", tone: "bg-[var(--color-accent-primary-subtle)]" },
  { key: "interviewing", label: "Interviewing", tone: "bg-[var(--color-accent-warning)]" },
  { key: "offer", label: "Offer", tone: "bg-[var(--color-accent-success)]" },
  { key: "accepted", label: "Accepted", tone: "bg-[var(--color-accent-success)]" },
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
    <Surface
      tone="subtle"
      padding="md"
      interactive
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
        "transition-transform duration-150 hover:-translate-y-1 hover:-translate-x-1",
        selected && "border-[var(--color-accent-primary)] bg-[var(--color-accent-primary-subtle)]"
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-text-muted">
            {application.status}
          </div>
          <h3 className="mt-2 truncate font-display text-lg font-black uppercase tracking-[-0.05em] text-foreground">
            {application.position_title ?? "Untitled application"}
          </h3>
          <div className="mt-2 flex items-center gap-1.5 text-xs text-muted-foreground">
            <Buildings size={12} weight="bold" />
            <span className="truncate">{application.company_name ?? "Unknown company"}</span>
          </div>
        </div>
        <div className="flex shrink-0 flex-col items-end gap-2">
          <Badge variant="outline">{application.status}</Badge>
          {application.updated_at ? (
            <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-text-muted">
              {formatDistanceToNow(new Date(application.updated_at), { addSuffix: true })}
            </span>
          ) : null}
        </div>
      </div>

      <div className="mt-4 flex items-center justify-between gap-3">
        <span className="text-xs text-text-muted">{application.source ?? "Unknown source"}</span>
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
          >
            Advance
          </Button>
        ) : (
          <Badge variant="success">Final</Badge>
        )}
      </div>
    </Surface>
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
  const tone =
    PIPELINE_STAGES.find((stage) => stage.key === keyName)?.tone ?? "bg-[var(--color-accent-primary)]";

  return (
    <Surface tone="default" padding="none" className="xl:min-w-[18rem] xl:flex-[0_0_18rem]">
      <div className={cn("h-2 border-b-2 border-border", tone)} />
      <div className="p-4">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <span className={cn("h-2.5 w-2.5 border border-border", tone)} />
            <span className="text-sm font-semibold uppercase tracking-[-0.04em] text-foreground">
              {label}
            </span>
          </div>
          <Badge variant="secondary">{applications.length}</Badge>
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
            <StateBlock
              tone="muted"
              title="No applications in this stage"
              description="Move work through the board to populate this lane."
            />
          )}
        </div>
      </div>
    </Surface>
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
  const selectedApplication =
    allApplications.find((application) => application.id === selectedApplicationId) ?? null;
  const firstApplicationId = allApplications[0]?.id ?? null;

  useEffect(() => {
    if (!selectedApplicationId && firstApplicationId) {
      setSelectedApplicationId(firstApplicationId);
    }
  }, [firstApplicationId, selectedApplicationId]);

  const transitionMutation = useMutation({
    mutationFn: async ({
      application,
      nextStatus,
    }: {
      application: Application;
      nextStatus: string;
    }) => {
      setAdvancingId(application.id);
      return pipelineApi.transition(application.id, {
        new_status: nextStatus,
        note: `Moved to ${nextStatus}`,
      });
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
      <PageHeader
        eyebrow="Execute"
        title="Pipeline"
        description="Track every application across the board, then promote a record with one click."
        meta={
          <>
            <Badge variant="info">{totalApplications.toLocaleString()} tracked</Badge>
            <Badge variant="warning">{interviewAndBeyond.toLocaleString()} late-stage</Badge>
          </>
        }
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
      />

      <MetricStrip
        items={[
          {
            key: "board-health",
            label: "Board health",
            value: totalApplications.toLocaleString(),
            icon: <Kanban size={18} weight="bold" />,
            tone: "default",
            hint: "Applications currently spread across the execution board.",
          },
          {
            key: "follow-up-load",
            label: "Follow-up load",
            value: followUpLoad.toLocaleString(),
            icon: <Clock size={18} weight="bold" />,
            tone: "warning",
            hint: "Items still needing a nudge or first response.",
          },
          {
            key: "late-stage-momentum",
            label: "Late-stage momentum",
            value: interviewAndBeyond.toLocaleString(),
            icon: <CheckCircle size={18} weight="bold" />,
            tone: "success",
            hint: "Applications already in interviews, offers, or accepted.",
          },
          {
            key: "selected",
            label: "Selected",
            value: selectedApplication ? selectedApplication.status : "None",
            icon: <Sparkle size={18} weight="bold" />,
            tone: "default",
            hint: "The record loaded into the detail pane.",
          },
        ]}
      />

      <SplitWorkspace
        primary={
          <Surface tone="default" padding="none" className="overflow-hidden">
            <div className="border-b-2 border-border bg-[var(--color-bg-tertiary)] px-5 py-4 sm:px-6">
              <div className="flex flex-wrap items-end justify-between gap-3">
                <div>
                  <div className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-text-muted">
                    Board
                  </div>
                  <h2 className="mt-1 font-display text-xl font-black uppercase tracking-[-0.05em] text-foreground sm:text-2xl">
                    Stage columns
                  </h2>
                </div>
                <Badge variant="secondary">Touch friendly</Badge>
              </div>
            </div>

            <div className="p-4">
              {isLoading ? (
                <div className="grid gap-4 md:grid-cols-2 xl:flex xl:overflow-x-auto">
                  {Array.from({ length: 6 }).map((_, index) => (
                    <div
                      key={index}
                      className="h-64 border-2 border-border bg-[var(--color-bg-tertiary)] xl:min-w-[18rem] xl:flex-[0_0_18rem]"
                    />
                  ))}
                </div>
              ) : isError ? (
                <StateBlock
                  tone="danger"
                  title="Failed to load the pipeline"
                  description="Try again after the backend finishes responding."
                />
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
          </Surface>
        }
        secondary={
          <Surface tone="default" padding="none" className="overflow-hidden xl:sticky xl:top-6">
            <div className="border-b-2 border-border bg-[var(--color-bg-tertiary)] px-5 py-4 sm:px-6">
              <div className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-text-muted">
                Selected application
              </div>
              <h2 className="mt-1 font-display text-xl font-black uppercase tracking-[-0.05em] text-foreground">
                Detail sheet
              </h2>
            </div>

            {selectedApplication ? (
              <div className="space-y-4 p-5 sm:p-6">
                <StateBlock
                  tone="muted"
                  title={selectedApplication.status}
                  description={`${selectedApplication.position_title ?? "Untitled application"}${selectedApplication.company_name ? ` · ${selectedApplication.company_name}` : ""}`}
                  icon={<Buildings size={18} weight="bold" />}
                />

                <div className="grid gap-3 sm:grid-cols-2">
                  <StateBlock
                    tone="muted"
                    title="Source"
                    description={selectedApplication.source ? `Source · ${selectedApplication.source}` : "Unknown"}
                  />
                  <StateBlock
                    tone="muted"
                    title="Salary"
                    description={
                      selectedApplication.salary_offered
                        ? `$${selectedApplication.salary_offered.toLocaleString()}`
                        : "Not recorded"
                    }
                  />
                </div>

                <StateBlock
                  tone="muted"
                  title="Notes"
                  description={
                    selectedApplication.notes ||
                    "No notes captured yet. Add context when you move the application forward."
                  }
                />

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
              <div className="p-5 sm:p-6">
                <StateBlock
                  tone="muted"
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
