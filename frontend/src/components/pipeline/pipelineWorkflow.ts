export const PIPELINE_STAGES = [
  { key: "saved", label: "Saved", tone: "bg-[var(--color-text-muted)]" },
  { key: "applied", label: "Applied", tone: "bg-[var(--color-accent-primary)]" },
  { key: "screening", label: "Screening", tone: "bg-[var(--color-accent-primary-subtle)]" },
  { key: "interviewing", label: "Interviewing", tone: "bg-[var(--color-accent-warning)]" },
  { key: "offer", label: "Offer", tone: "bg-[var(--color-accent-success)]" },
  { key: "accepted", label: "Accepted", tone: "bg-[var(--color-accent-success)]" },
] as const;

export const NEXT_STAGE: Record<string, string | undefined> = {
  saved: "applied",
  applied: "screening",
  screening: "interviewing",
  interviewing: "offer",
  offer: "accepted",
};
