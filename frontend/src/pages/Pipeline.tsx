import { CheckCircle, Clock, Kanban, Play, Sparkle } from "@phosphor-icons/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { pipelineApi, type Application } from "../api/pipeline";
import Badge from "../components/ui/Badge";
import Button from "../components/ui/Button";
import { MetricStrip, PageHeader, SplitWorkspace } from "../components/system";
import KanbanBoard from "../components/pipeline/KanbanBoard";
import { PipelineBoard } from "../components/pipeline/PipelineBoard";
import { PipelineDetailPanel } from "../components/pipeline/PipelineDetailPanel";
import { NEXT_STAGE, PIPELINE_STAGES, getAllowedTransitions } from "../components/pipeline/pipelineWorkflow";

export default function Pipeline() {
  const navigate = useNavigate();
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
        description="Track applications by stage."
        meta={
          <>
            <Badge variant="info">{totalApplications.toLocaleString()} tracked</Badge>
            <Badge variant="warning">{interviewAndBeyond.toLocaleString()} late-stage</Badge>
          </>
        }
        actions={
          <>
            <Button
              variant="secondary"
              icon={<Play size={16} weight="bold" />}
              onClick={() => navigate("/auto-apply")}
            >
              Auto-apply
            </Button>
            <Button
              variant="primary"
              icon={<Sparkle size={16} weight="bold" />}
              onClick={() => navigate("/copilot")}
            >
              Copilot
            </Button>
          </>
        }
      />

      <MetricStrip
        items={[
          {
            key: "applications",
            label: "Applications",
            value: totalApplications.toLocaleString(),
            icon: <Kanban size={18} weight="bold" />,
            tone: "default",
            hint: "Total on board.",
          },
          {
            key: "follow-up",
            label: "Follow-up",
            value: followUpLoad.toLocaleString(),
            icon: <Clock size={18} weight="bold" />,
            tone: "warning",
            hint: "Needs attention.",
          },
          {
            key: "late-stage",
            label: "Late stage",
            value: interviewAndBeyond.toLocaleString(),
            icon: <CheckCircle size={18} weight="bold" />,
            tone: "success",
            hint: "Interview or later.",
          },
          {
            key: "selected",
            label: "Selected",
            value: selectedApplication ? selectedApplication.status : "None",
            icon: <Sparkle size={18} weight="bold" />,
            tone: "default",
            hint: "Open in detail pane.",
          },
        ]}
      />

      <SplitWorkspace
        primary={
          <KanbanBoard
            apps={allApplications}
            onDragTransition={(appId, newStatus) => {
              const application = allApplications.find((item) => item.id === appId);
              if (!application || application.status === newStatus) {
                return;
              }
              if (!getAllowedTransitions(application.status).includes(newStatus)) {
                return;
              }
              transitionMutation.mutate({ application, nextStatus: newStatus });
            }}
          >
            <PipelineBoard
              isLoading={isLoading}
              isError={isError}
              stageColumns={stageColumns}
              selectedApplicationId={selectedApplicationId}
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
          </KanbanBoard>
        }
        secondary={
          <PipelineDetailPanel
            selectedApplication={selectedApplication}
            firstApplicationId={firstApplicationId}
            advancingId={advancingId}
            onTransition={(application, nextStatus) => {
              if (!nextStatus) {
                return;
              }
              transitionMutation.mutate({ application, nextStatus });
            }}
            onSelectFirst={() => {
              if (firstApplicationId) {
                setSelectedApplicationId(firstApplicationId);
              }
            }}
          />
        }
      />
    </div>
  );
}
