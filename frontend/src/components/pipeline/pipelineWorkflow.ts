export const PIPELINE_STAGES = [
  { key: "saved", label: "Saved", tone: "bg-[var(--color-text-muted)]" },
  { key: "applied", label: "Applied", tone: "bg-[var(--color-accent-primary)]" },
  { key: "screening", label: "Screening", tone: "bg-[var(--color-accent-primary-subtle)]" },
  { key: "interviewing", label: "Interviewing", tone: "bg-[var(--color-accent-warning)]" },
  { key: "offer", label: "Offer", tone: "bg-[var(--color-accent-success)]" },
  { key: "accepted", label: "Accepted", tone: "bg-[var(--color-accent-success)]" },
  { key: "rejected", label: "Rejected", tone: "bg-[var(--color-accent-danger)]" },
  { key: "withdrawn", label: "Withdrawn", tone: "bg-[var(--color-text-muted)]" },
] as const;

export const NEXT_STAGE: Record<string, string | undefined> = {
  saved: "applied",
  applied: "screening",
  screening: "interviewing",
  interviewing: "offer",
  offer: "accepted",
};

export const VALID_TRANSITIONS: Record<string, string[]> = {
  saved: ["applied", "withdrawn"],
  applied: ["screening", "interviewing", "rejected", "withdrawn"],
  screening: ["interviewing", "rejected", "withdrawn"],
  interviewing: ["offer", "rejected", "withdrawn"],
  offer: ["accepted", "rejected", "withdrawn"],
  accepted: [],
  rejected: ["saved"],
  withdrawn: ["saved"],
};

export const STAGE_LABELS: Record<string, string> = {
  saved: "Saved",
  applied: "Applied",
  screening: "Screening",
  interviewing: "Interviewing",
  offer: "Offer",
  accepted: "Accepted",
  rejected: "Rejected",
  withdrawn: "Withdrawn",
};

export function getAllowedTransitions(status: string) {
  return VALID_TRANSITIONS[status] ?? [];
}
