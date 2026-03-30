import { ArrowClockwise, CheckCircle, XCircle } from "@phosphor-icons/react";
import { formatDistanceToNow } from "date-fns";

export function relativeTime(dateStr: string | null): string {
  if (!dateStr) return "never";
  try {
    return formatDistanceToNow(new Date(dateStr), { addSuffix: true });
  } catch {
    return "unknown";
  }
}

export function priorityVariant(
  pc: string
): "warning" | "danger" | "info" | "default" {
  switch (pc) {
    case "watchlist":
      return "warning";
    case "hot":
      return "danger";
    case "warm":
      return "info";
    default:
      return "default";
  }
}

export function atsVariant(vendor: string | null): "success" | "default" {
  if (!vendor || vendor === "unknown") return "default";
  return "success";
}

export function attemptStatusIcon(status: string) {
  if (status === "success") {
    return <CheckCircle size={14} weight="fill" className="text-accent-success" />;
  }
  if (status === "failure" || status === "error") {
    return <XCircle size={14} weight="fill" className="text-accent-danger" />;
  }
  return <ArrowClockwise size={14} weight="bold" className="text-text-muted" />;
}
