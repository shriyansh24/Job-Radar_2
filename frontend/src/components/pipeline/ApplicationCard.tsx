import {
  Buildings,
  Clock,
  DotsThreeVertical,
  ClockCounterClockwise,
} from "@phosphor-icons/react";
import { formatDistanceToNow } from "date-fns";
import type { Application } from "../../api/pipeline";
import Badge from "../ui/Badge";
import Card from "../ui/Card";
import Dropdown from "../ui/Dropdown";

const STATUS_TRANSITIONS: Record<string, string[]> = {
  saved: ["applied", "withdrawn"],
  applied: ["screening", "rejected", "withdrawn"],
  screening: ["interviewing", "rejected", "withdrawn"],
  interviewing: ["offer", "rejected", "withdrawn"],
  offer: ["accepted", "rejected", "withdrawn"],
  accepted: [],
  rejected: [],
  withdrawn: [],
};

export function statusBadgeVariant(
  status: string
): "default" | "success" | "warning" | "danger" | "info" {
  switch (status) {
    case "offer":
    case "accepted":
      return "success";
    case "interviewing":
      return "warning";
    case "rejected":
      return "danger";
    case "applied":
    case "screening":
      return "info";
    default:
      return "default";
  }
}

interface ApplicationCardProps {
  app: Application;
  onTransition: (newStatus: string) => void;
  onViewHistory: () => void;
}

export default function ApplicationCard({ app, onTransition, onViewHistory }: ApplicationCardProps) {
  const transitions = STATUS_TRANSITIONS[app.status] || [];

  return (
    <Card hover padding="sm" className="mb-2">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="text-sm font-medium text-text-primary truncate">{app.position_title}</p>
          <p className="text-xs text-text-secondary flex items-center gap-1 mt-0.5">
            <Buildings size={12} weight="bold" />
            {app.company_name}
          </p>
        </div>
        {transitions.length > 0 && (
          <Dropdown
            align="right"
            trigger={
              <button
                className="p-1.5 rounded-[var(--radius-sm)] hover:bg-bg-tertiary text-text-muted transition-[background-color,transform] duration-[var(--transition-fast)] active:translate-y-[1px]"
                aria-label="Application actions"
              >
                <DotsThreeVertical size={16} weight="bold" />
              </button>
            }
            items={[
              ...transitions.map((s) => ({ label: `Move to ${s}`, value: s })),
              {
                label: "View History",
                value: "_history",
                icon: <ClockCounterClockwise size={14} weight="bold" />,
              },
            ]}
            onSelect={(val) => {
              if (val === "_history") onViewHistory();
              else onTransition(val);
            }}
          />
        )}
      </div>
      <div className="flex items-center gap-2 mt-2">
        <Badge variant={statusBadgeVariant(app.status)} size="sm">{app.status}</Badge>
        {app.applied_at && (
          <span className="text-xs text-text-muted flex items-center gap-1">
            <Clock size={12} weight="bold" />
            {formatDistanceToNow(new Date(app.applied_at), { addSuffix: true })}
          </span>
        )}
      </div>
      {app.notes && (
        <p className="text-xs text-text-muted mt-2 truncate">{app.notes}</p>
      )}
    </Card>
  );
}
