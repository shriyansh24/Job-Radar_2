import type { ReferralSuggestion } from "../../api/networking";
import Badge from "../ui/Badge";
import { Button } from "../ui/Button";

const PANEL_ALT =
  "border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-primary)]";
const SECONDARY_BUTTON =
  "!rounded-none !border-2 !border-[var(--color-text-primary)] !bg-[var(--color-bg-secondary)] !text-[var(--color-text-primary)] !shadow-none";
const PRIMARY_BUTTON =
  "!rounded-none !border-2 !border-[var(--color-text-primary)] !bg-[var(--color-accent-primary)] !text-white !shadow-none";

export function SuggestionCard({
  suggestion,
  selectedJobId,
  onDraft,
  onCreate,
}: {
  suggestion: ReferralSuggestion;
  selectedJobId: string;
  onDraft: (contactId: string) => void;
  onCreate: (contactId: string, message?: string | null) => void;
}) {
  return (
    <div className={`${PANEL_ALT} p-4`}>
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-sm font-bold uppercase tracking-[0.08em]">{suggestion.contact.name}</div>
          <div className="mt-1 text-sm text-[var(--color-text-secondary)]">
            {[suggestion.contact.role, suggestion.contact.company].filter(Boolean).join(" - ")}
          </div>
        </div>
        <Badge variant="success" className="rounded-none">
          Suggested
        </Badge>
      </div>
      <p className="mt-3 text-sm leading-6 text-[var(--color-text-secondary)]">{suggestion.relevance_reason}</p>
      {suggestion.suggested_message ? (
        <div className="mt-3 border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-primary)] px-3 py-3 text-sm leading-6">
          {suggestion.suggested_message}
        </div>
      ) : null}
      <div className="mt-4 flex flex-wrap gap-2">
        <Button variant="secondary" className={SECONDARY_BUTTON} onClick={() => onDraft(suggestion.contact.id)}>
          Draft outreach
        </Button>
        <Button
          variant="default"
          className={PRIMARY_BUTTON}
          onClick={() => onCreate(suggestion.contact.id, suggestion.suggested_message ?? null)}
        >
          Create request
        </Button>
      </div>
      <div className="mt-3 text-[10px] font-bold uppercase tracking-[0.2em] text-[var(--color-text-muted)]">
        Target job {selectedJobId.slice(0, 12)}
      </div>
    </div>
  );
}
