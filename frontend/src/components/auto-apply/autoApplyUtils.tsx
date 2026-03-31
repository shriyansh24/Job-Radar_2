export const CHIP =
  "inline-flex items-center gap-1 border-2 border-[var(--color-text-primary)] px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.18em]";

export function statusVariant(status: string): "success" | "danger" | "warning" | "info" | "default" {
  switch (status) {
    case "completed":
    case "success":
    case "submitted":
      return "success";
    case "filled":
    case "failed":
      return status === "failed" ? "danger" : "warning";
    case "queued":
    case "pending":
      return "warning";
    case "running":
      return "info";
    default:
      return "default";
  }
}
