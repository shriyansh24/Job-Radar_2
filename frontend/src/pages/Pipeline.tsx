import { Plus } from "@phosphor-icons/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { pipelineApi, type Application } from "../api/pipeline";
import AddApplicationModal from "../components/pipeline/AddApplicationModal";
import ApplicationModal from "../components/pipeline/ApplicationModal";
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
    onSuccess: () => {
      toast('success', 'Status updated');
      queryClient.invalidateQueries({ queryKey: ['pipeline'] });
    },
    onError: () => toast('error', 'Invalid transition'),
  });

  const totalApps = COLUMNS.reduce(
    (sum, col) => sum + (pipelineData?.[col.key]?.length || 0),
    0
  );

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
        <div className="flex gap-4 h-full min-w-max pb-4 pr-1">
          {COLUMNS.map((col) => (
            <PipelineColumn
              key={col.key}
              label={col.label}
              color={col.color}
              apps={(pipelineData?.[col.key] || []) as Application[]}
              loading={isLoading}
              onTransition={(appId, newStatus) =>
                transitionMutation.mutate({ id: appId, newStatus })
              }
              onViewHistory={(app) => setHistoryApp(app)}
            />
          ))}
        </div>
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
