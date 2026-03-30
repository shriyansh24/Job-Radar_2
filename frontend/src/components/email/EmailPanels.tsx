import {
  ArrowClockwise,
  Buildings,
  CheckCircle,
  EnvelopeSimple,
  Funnel,
  Sparkle,
} from "@phosphor-icons/react";
import { formatDistanceToNow } from "date-fns";
import type { EmailLog, EmailWebhookPayload, EmailWebhookResponse } from "../../api/email";
import { cn } from "../../lib/utils";
import Badge from "../ui/Badge";
import Button from "../ui/Button";
import EmptyState from "../ui/EmptyState";
import Input from "../ui/Input";
import Select from "../ui/Select";
import Skeleton from "../ui/Skeleton";
import Textarea from "../ui/Textarea";

const PANEL =
  "border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-secondary)] shadow-none";
const PANEL_ALT =
  "border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-primary)] shadow-none";
const FIELD =
  "!rounded-none !border-2 !border-[var(--color-text-primary)] !bg-[var(--color-bg-secondary)] !text-[var(--color-text-primary)] placeholder:!text-[var(--color-text-muted)] !shadow-none focus:!border-[var(--color-accent-primary)] focus:!ring-0";
const PRIMARY_BUTTON =
  "!rounded-none !border-2 !border-[var(--color-text-primary)] !bg-[var(--color-accent-primary)] !text-white !shadow-none";

export function EmailSignalList({
  isLoading,
  filteredLogs,
  selectedLogId,
  searchValue,
  actionFilter,
  filterOptions,
  onSearchChange,
  onActionFilterChange,
  onSelect,
}: {
  isLoading: boolean;
  filteredLogs: EmailLog[];
  selectedLogId: string | null;
  searchValue: string;
  actionFilter: string;
  filterOptions: { value: string; label: string }[];
  onSearchChange: (value: string) => void;
  onActionFilterChange: (value: string) => void;
  onSelect: (id: string) => void;
}) {
  return (
    <div className={`${PANEL} overflow-hidden`}>
      <div className="border-b-2 border-[var(--color-text-primary)] px-5 py-4">
        <div className="text-sm font-bold uppercase tracking-[0.2em]">Signal log</div>
        <div className="mt-4 grid gap-3 md:grid-cols-[minmax(0,1fr)_180px]">
          <Input
            value={searchValue}
            onChange={(event) => onSearchChange(event.target.value)}
            placeholder="Search sender, subject, company, or title"
            icon={<Funnel size={16} weight="bold" />}
            className={FIELD}
          />
          <Select
            value={actionFilter}
            onChange={(event) => onActionFilterChange(event.target.value)}
            options={filterOptions}
            className={FIELD}
          />
        </div>
      </div>

      <div className="max-h-[72vh] overflow-auto p-3">
        {isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 7 }).map((_, index) => (
              <Skeleton key={index} variant="rect" className="h-24 w-full" />
            ))}
          </div>
        ) : filteredLogs.length ? (
          <div className="space-y-3">
            {filteredLogs.map((log) => (
              <button
                key={log.id}
                type="button"
                onClick={() => onSelect(log.id)}
                className={cn(
                  "w-full border-2 px-4 py-4 text-left transition-transform duration-150",
                  selectedLogId === log.id
                    ? "border-[var(--color-text-primary)] bg-[var(--color-accent-primary-subtle)] shadow-none"
                    : "border-[var(--color-text-primary)] bg-[var(--color-bg-secondary)] shadow-none hover:-translate-x-[2px] hover:-translate-y-[2px]"
                )}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="truncate text-sm font-bold uppercase tracking-[0.08em]">
                      {log.subject}
                    </div>
                    <div className="mt-1 truncate text-sm text-[var(--color-text-secondary)]">
                      {log.sender}
                    </div>
                  </div>
                  <Badge variant={log.parsed_action ? "info" : "default"} className="rounded-none">
                    {log.parsed_action ?? "unknown"}
                  </Badge>
                </div>
                <div className="mt-3 flex flex-wrap items-center gap-3 text-xs text-[var(--color-text-muted)]">
                  {log.company_extracted ? (
                    <span className="flex items-center gap-1">
                      <Buildings size={12} weight="bold" />
                      {log.company_extracted}
                    </span>
                  ) : null}
                  <span>{formatDistanceToNow(new Date(log.created_at), { addSuffix: true })}</span>
                  {log.confidence !== null ? <span>{Math.round(log.confidence * 100)}% confidence</span> : null}
                </div>
              </button>
            ))}
          </div>
        ) : (
          <EmptyState
            icon={<EnvelopeSimple size={32} weight="bold" />}
            title="No matching signals"
            description="Adjust the filter or search to widen the log."
          />
        )}
      </div>
    </div>
  );
}

export function EmailSignalDetail({
  selectedLog,
}: {
  selectedLog: EmailLog | null;
}) {
  return (
    <div className={`${PANEL} p-5 sm:p-6`}>
      <div className="flex items-center gap-2 text-sm font-bold uppercase tracking-[0.18em]">
        <Funnel size={16} weight="bold" className="text-[var(--color-accent-primary)]" />
        Signal detail
      </div>
      {selectedLog ? (
        <div className="mt-4 space-y-4">
          <div className={`${PANEL_ALT} px-4 py-4`}>
            <div className="text-lg font-black uppercase tracking-tighter">{selectedLog.subject}</div>
            <div className="mt-2 text-sm text-[var(--color-text-secondary)]">{selectedLog.sender}</div>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <div className={`${PANEL_ALT} px-4 py-4`}>
              <div className="text-[10px] font-bold uppercase tracking-[0.22em] text-[var(--color-text-muted)]">
                Action
              </div>
              <div className="mt-2 text-base font-bold">{selectedLog.parsed_action ?? "No structured action"}</div>
              <div className="mt-2 text-sm text-[var(--color-text-secondary)]">
                Confidence {selectedLog.confidence !== null ? `${Math.round(selectedLog.confidence * 100)}%` : "not available"}
              </div>
            </div>
            <div className={`${PANEL_ALT} px-4 py-4`}>
              <div className="text-[10px] font-bold uppercase tracking-[0.22em] text-[var(--color-text-muted)]">
                Match
              </div>
              <div className="mt-2 break-all text-sm">{selectedLog.matched_application_id ?? "No application match"}</div>
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <div className={`${PANEL_ALT} px-4 py-4`}>
              <div className="text-[10px] font-bold uppercase tracking-[0.22em] text-[var(--color-text-muted)]">
                Company
              </div>
              <div className="mt-2 text-sm">{selectedLog.company_extracted ?? "Unknown"}</div>
            </div>
            <div className={`${PANEL_ALT} px-4 py-4`}>
              <div className="text-[10px] font-bold uppercase tracking-[0.22em] text-[var(--color-text-muted)]">
                Job title
              </div>
              <div className="mt-2 text-sm">{selectedLog.job_title_extracted ?? "Unknown"}</div>
            </div>
          </div>

          <div className={`${PANEL_ALT} px-4 py-4 text-sm leading-6 text-[var(--color-text-secondary)]`}>
            Processed {formatDistanceToNow(new Date(selectedLog.processed_at), { addSuffix: true })}. Use this panel to check the parsed result.
          </div>
        </div>
      ) : (
        <EmptyState
          icon={<EnvelopeSimple size={32} weight="bold" />}
          title="Choose a log entry"
          description="Select a signal from the left to inspect the parsed result."
        />
      )}
    </div>
  );
}

export function EmailReplayPanel({
  replayForm,
  replayResult,
  pending,
  onChange,
  onSubmit,
}: {
  replayForm: EmailWebhookPayload;
  replayResult: EmailWebhookResponse | null;
  pending: boolean;
  onChange: (value: EmailWebhookPayload) => void;
  onSubmit: () => void;
}) {
  return (
    <div className={`${PANEL} p-5 sm:p-6`}>
      <div className="flex items-center gap-2 text-sm font-bold uppercase tracking-[0.18em]">
        <Sparkle size={16} weight="bold" className="text-[var(--color-accent-warning)]" />
        Replay signal
      </div>
      <p className="mt-1 text-sm leading-6 text-[var(--color-text-secondary)]">
        Send a webhook-shaped payload to test parsing or backfill a missed signal.
      </p>
      <div className="mt-4 grid gap-4 md:grid-cols-2">
        <Input
          label="Sender"
          value={replayForm.sender ?? ""}
          onChange={(event) => onChange({ ...replayForm, sender: event.target.value })}
          placeholder="recruiter@company.com"
          className={FIELD}
        />
        <Input
          label="From"
          value={replayForm.from_ ?? ""}
          onChange={(event) => onChange({ ...replayForm, from_: event.target.value })}
          placeholder="Optional override"
          className={FIELD}
        />
      </div>
      <Input
        className={`${FIELD} mt-4`}
        label="Subject"
        value={replayForm.subject ?? ""}
        onChange={(event) => onChange({ ...replayForm, subject: event.target.value })}
        placeholder="Interview invitation"
      />
      <Textarea
        className={`${FIELD} mt-4 min-h-[160px]`}
        label="Body"
        value={replayForm.text ?? ""}
        onChange={(event) => onChange({ ...replayForm, text: event.target.value })}
        placeholder="Paste the inbound email body here."
      />
      <div className="mt-4 flex justify-end">
        <Button variant="default" className={PRIMARY_BUTTON} onClick={onSubmit} disabled={pending}>
          <ArrowClockwise size={16} weight="bold" />
          Process signal
        </Button>
      </div>

      {replayResult ? (
        <div className={`${PANEL_ALT} mt-4 px-4 py-4`}>
          <div className="flex items-start justify-between gap-3">
            <div>
              <div className="text-sm font-bold uppercase tracking-[0.08em]">{replayResult.status}</div>
              <p className="mt-1 text-sm text-[var(--color-text-secondary)]">
                {replayResult.message ?? "Signal processed."}
              </p>
            </div>
            <Badge variant={replayResult.status === "updated" ? "success" : "info"} className="rounded-none">
              {replayResult.action ?? "no action"}
            </Badge>
          </div>
          <div className="mt-3 flex flex-wrap gap-3 text-xs text-[var(--color-text-muted)]">
            {replayResult.company ? <span>Company: {replayResult.company}</span> : null}
            {replayResult.application_id ? <span>Application: {replayResult.application_id}</span> : null}
            {replayResult.confidence !== null ? <span>Confidence: {Math.round(replayResult.confidence * 100)}%</span> : null}
          </div>
        </div>
      ) : null}
    </div>
  );
}

export function EmailNotesPanel() {
  return (
    <div className={`${PANEL_ALT} p-5 sm:p-6`}>
      <div className="flex items-center gap-2 text-sm font-bold uppercase tracking-[0.18em]">
        <CheckCircle size={16} weight="bold" className="text-[var(--color-accent-success)]" />
        Operating notes
      </div>
      <div className="mt-3 space-y-2 text-sm leading-6 text-[var(--color-text-secondary)]">
        <p>Use this page for inbound hiring communication, not as a general inbox.</p>
        <p>Unknown actions are still useful if the extracted company and title are correct.</p>
        <p>Replay stays visible so manual cleanup is always available.</p>
      </div>
    </div>
  );
}
