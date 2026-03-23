import { Plus } from "@phosphor-icons/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useCallback, useState } from "react";
import { pipelineApi, type Application } from "../api/pipeline";
import AddApplicationModal from "../components/pipeline/AddApplicationModal";
import ApplicationModal from "../components/pipeline/ApplicationModal";
import KanbanBoard from "../components/pipeline/KanbanBoard";
import PipelineColumn from "../components/pipeline/PipelineColumn";
import Button from "../components/ui/Button";
import { toast } from "../components/ui/toastService";

const COLUMNS = [
  { key: "saved", label: "Saved", color: "border-text-muted" },
  { key: "applied", label: "Applied", color: "border-accent-primary" },
  { key: "screening", label: "Screening", color: "border-accent-primary/60" },
  { key: "interviewing", label: "Interviewing", color: "border-accent-warning" },
  { key: "offer", label: "Offer", color: "border-accent-success" },
  { key: "accepted", label: "Accepted", color: "border-accent-success" },
  { key: "rejected", label: "Rejected", color: "border-accent-danger" },
  { key: "withdrawn", label: "Withdrawn", color: "border-text-muted" },
];

export default function Pipeline() {
  const queryClient = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const [historyApp, setHistoryApp] = useState<Application | null>(null);

  const { data: pipelineData, isLoading } = useQuery({
    queryKey: ["pipeline"],
    queryFn: () => pipelineApi.pipeline().then((r) => r.data),
  });

  const transitionMutation = useMutation({
    mutationFn: ({ id, newStatus }: { id: string; newStatus: string }) =>
      pipelineApi.transition(id, { new_status: newStatus }),
    onMutate: async ({ id, newStatus }) => {
      // Cancel any outgoing refetches so they don't overwrite our optimistic update
      await queryClient.cancelQueries({ queryKey: ["pipeline"] });

      const previous =
        queryClient.getQueryData<Record<string, Application[]>>(["pipeline"]);

      // Optimistic update: move the app between columns
      if (previous) {
        const updated = { ...previous };
        let movedApp: Application | undefined;

        // Find and remove from current column
        for (const key of Object.keys(updated)) {
          const idx = updated[key]?.findIndex((a) => a.id === id);
          if (idx !== undefined && idx >= 0 && updated[key]) {
            movedApp = { ...updated[key][idx], status: newStatus };
            updated[key] = updated[key].filter((_, i) => i !== idx);
            break;
          }
        }

        // Add to new column
        if (movedApp) {
          updated[newStatus] = [...(updated[newStatus] || []), movedApp];
        }

        queryClient.setQueryData(["pipeline"], updated);
      }

      return { previous };
    },
    onSuccess: () => {
      toast("success", "Status updated");
    },
    onError: (_err, _vars, context) => {
      // Rollback on failure
      if (context?.previous) {
        queryClient.setQueryData(["pipeline"], context.previous);
      }
      toast("error", "Invalid transition");
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["pipeline"] });
    },
  });

  const handleTransition = useCallback(
    (appId: string, newStatus: string) => {
      transitionMutation.mutate({ id: appId, newStatus });
    },
    [transitionMutation],
  );

  // Collect all apps for the drag overlay
  const allApps: Application[] = pipelineData
    ? COLUMNS.flatMap((col) => (pipelineData[col.key] || []) as Application[])
    : [];

  const totalApps = allApps.length;

  return (
    <div className="flex flex-col min-h-0 gap-4">
      <div className="flex items-end justify-between shrink-0">
        <div>
          <div className="text-xs font-medium text-text-muted tracking-tight">
            Pipeline
          </div>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight text-text-primary">
            Applications
          </h1>
          <p className="mt-1 text-sm text-text-secondary">
            <span className="font-mono">{totalApps}</span> total
          </p>
        </div>
        <Button
          variant="primary"
          onClick={() => setShowCreate(true)}
          icon={<Plus size={16} weight="bold" />}
        >
          Add Application
        </Button>
      </div>

      <div className="flex-1 min-h-0 overflow-x-auto">
        <KanbanBoard
          onDragTransition={handleTransition}
          apps={allApps}
        >
          <div className="flex gap-4 h-full min-w-max pb-4 pr-1">
            {COLUMNS.map((col) => (
              <PipelineColumn
                key={col.key}
                columnId={col.key}
                label={col.label}
                color={col.color}
                apps={(pipelineData?.[col.key] || []) as Application[]}
                loading={isLoading}
                onTransition={handleTransition}
                onViewHistory={(app) => setHistoryApp(app)}
              />
            ))}
          </div>
        </KanbanBoard>
      </div>

      <AddApplicationModal open={showCreate} onClose={() => setShowCreate(false)} />
      <ApplicationModal
        open={!!historyApp}
        onClose={() => setHistoryApp(null)}
        application={historyApp}
      />
    </div>
  );
}
