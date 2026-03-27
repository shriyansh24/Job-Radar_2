import { Handshake } from "@phosphor-icons/react";
import type { ReferralSuggestion } from "../../api/networking";
import Badge from "../ui/Badge";
import { Button } from "../ui/Button";
import EmptyState from "../ui/EmptyState";
import Select from "../ui/Select";
import Textarea from "../ui/Textarea";

const PANEL =
  "border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-secondary)]";
const PANEL_ALT =
  "border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-primary)]";
const FIELD =
  "!rounded-none !border-2 !border-[var(--color-text-primary)] !bg-[var(--color-bg-secondary)] !text-[var(--color-text-primary)] placeholder:!text-[var(--color-text-muted)] !shadow-none focus:!border-[var(--color-accent-primary)] focus:!ring-0";
const SECONDARY_BUTTON =
  "!rounded-none !border-2 !border-[var(--color-text-primary)] !bg-[var(--color-bg-secondary)] !text-[var(--color-text-primary)] !shadow-none";
const PRIMARY_BUTTON =
  "!rounded-none !border-2 !border-[var(--color-text-primary)] !bg-[var(--color-accent-primary)] !text-white !shadow-none";

export function NetworkingReferralDeskPanel({
  selectedJobId,
  setSelectedJobId,
  jobOptions,
  suggestions,
  onSuggest,
  onDraft,
  onCreate,
  generatedMessage,
  setGeneratedMessage,
  selectedJobLabel,
  pendingSuggestions,
}: {
  selectedJobId: string;
  setSelectedJobId: (value: string) => void;
  jobOptions: Array<{ value: string; label: string }>;
  suggestions: ReferralSuggestion[];
  onSuggest: () => void;
  onDraft: (contactId: string) => void;
  onCreate: (contactId: string, message?: string | null) => void;
  generatedMessage: string;
  setGeneratedMessage: (value: string) => void;
  selectedJobLabel: string | null;
  pendingSuggestions: boolean;
}) {
  return (
    <div className={`${PANEL} p-5 sm:p-6`}>
      <div className="text-sm font-bold uppercase tracking-[0.2em]">Referral desk</div>
      <p className="mt-2 text-sm leading-6 text-[var(--color-text-secondary)]">
        Pick a job, get likely referral paths, and draft outreach.
      </p>
      <div className="mt-4 space-y-4">
        <Select
          label="Target job"
          value={selectedJobId}
          onChange={(event) => setSelectedJobId(event.target.value)}
          options={jobOptions}
          placeholder="Choose a job"
          className={FIELD}
        />
        <Button
          variant="secondary"
          className={SECONDARY_BUTTON}
          onClick={onSuggest}
          disabled={!selectedJobId || pendingSuggestions}
        >
          <Handshake size={16} weight="bold" />
          Suggest referrals
        </Button>
      </div>

      <div className="mt-4 space-y-3">
        {suggestions.length ? (
          suggestions.map((suggestion) => (
            <div key={suggestion.contact.id} className={`${PANEL_ALT} p-4`}>
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
          ))
        ) : (
          <EmptyState
            icon={<Handshake size={28} weight="bold" />}
            title="No referral suggestions loaded"
            description="Choose a job and ask for the warmest available path."
          />
        )}
      </div>

      {generatedMessage ? (
        <Textarea
          label="Generated outreach"
          className={`${FIELD} mt-4 min-h-[160px]`}
          value={generatedMessage}
          onChange={(event) => setGeneratedMessage(event.target.value)}
        />
      ) : null}
      {selectedJobLabel ? (
        <p className="mt-3 text-xs font-bold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">
          Current target: {selectedJobLabel}
        </p>
      ) : null}
    </div>
  );
}
