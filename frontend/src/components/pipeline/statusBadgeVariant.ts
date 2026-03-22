export function statusBadgeVariant(
  status: string,
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
