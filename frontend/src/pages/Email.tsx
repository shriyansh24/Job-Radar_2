import {
  ArrowClockwise,
  Buildings,
  CheckCircle,
  EnvelopeSimple,
  Funnel,
  MagnifyingGlass,
  Sparkle,
} from "@phosphor-icons/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { formatDistanceToNow } from "date-fns";
import { useDeferredValue, useEffect, useState } from "react";
import { emailApi, type EmailWebhookPayload, type EmailWebhookResponse } from "../api/email";
import { MetricStrip } from "../components/system/MetricStrip";
import { PageHeader } from "../components/system/PageHeader";
import Badge from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import EmptyState from "../components/ui/EmptyState";
import Input from "../components/ui/Input";
import Select from "../components/ui/Select";
import Skeleton from "../components/ui/Skeleton";
import Textarea from "../components/ui/Textarea";
import { toast } from "../components/ui/toastService";
import { cn } from "../lib/utils";

const FILTER_OPTIONS = [
  { value: "all", label: "All actions" },
  { value: "interview", label: "Interview" },
  { value: "rejection", label: "Rejection" },
  { value: "offer", label: "Offer" },
  { value: "follow_up", label: "Follow-up" },
  { value: "unknown", label: "Unknown" },
];

const emptyReplay: EmailWebhookPayload = {
  sender: "",
  from_: "",
  to: "",
  subject: "",
  text: "",
};

const PANEL =
  "border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-secondary)] shadow-[4px_4px_0px_0px_var(--color-text-primary)]";
const PANEL_ALT =
  "border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-primary)] shadow-[4px_4px_0px_0px_var(--color-text-primary)]";
const FIELD =
  "!rounded-none !border-2 !border-[var(--color-text-primary)] !bg-[var(--color-bg-secondary)] !text-[var(--color-text-primary)] placeholder:!text-[var(--color-text-muted)] !shadow-none focus:!border-[var(--color-accent-primary)] focus:!ring-0";
const PRIMARY_BUTTON =
  "!rounded-none !border-2 !border-[var(--color-text-primary)] !bg-[var(--color-accent-primary)] !text-white !shadow-[4px_4px_0px_0px_var(--color-text-primary)]";

export default function Email() {
  const queryClient = useQueryClient();
  const [searchValue, setSearchValue] = useState("");
  const [actionFilter, setActionFilter] = useState("all");
  const [selectedLogId, setSelectedLogId] = useState<string | null>(null);
  const [replayForm, setReplayForm] = useState<EmailWebhookPayload>({ ...emptyReplay });
  const [replayResult, setReplayResult] = useState<EmailWebhookResponse | null>(null);
  const deferredSearch = useDeferredValue(searchValue);

  const { data: logs, isLoading } = useQuery({
    queryKey: ["email", "logs"],
    queryFn: () => emailApi.listLogs(100).then((response) => response.data),
  });

  useEffect(() => {
    if (!selectedLogId && logs?.length) {
      setSelectedLogId(logs[0].id);
    }
  }, [logs, selectedLogId]);

  const filteredLogs =
    logs?.filter((log) => {
      const query = deferredSearch.trim().toLowerCase();
      const action = log.parsed_action ?? "unknown";
      const matchesFilter = actionFilter === "all" || action === actionFilter;
      if (!matchesFilter) return false;
      if (!query) return true;
      return [log.sender, log.subject, log.company_extracted, log.job_title_extracted, log.parsed_action]
        .filter(Boolean)
        .some((value) => value?.toLowerCase().includes(query));
    }) ?? [];

  const selectedLog =
    filteredLogs.find((log) => log.id === selectedLogId) ??
    logs?.find((log) => log.id === selectedLogId) ??
    null;

  const replayMutation = useMutation({
    mutationFn: (payload: EmailWebhookPayload) => emailApi.processWebhook(payload).then((response) => response.data),
    onSuccess: (response) => {
      setReplayResult(response);
      toast("success", "Email signal processed");
      queryClient.invalidateQueries({ queryKey: ["email", "logs"] });
    },
    onError: () => toast("error", "Failed to process email signal"),
  });

  const actionableLogs = logs?.filter((log) => log.parsed_action && log.parsed_action !== "unknown") ?? [];
  const avgConfidence =
    logs?.length && logs.some((log) => log.confidence !== null)
      ? `${Math.round((logs.reduce((sum, log) => sum + (log.confidence ?? 0), 0) / logs.length) * 100)}%`
      : "0%";

  const submitReplay = () => {
    if (!replayForm.sender?.trim() || !replayForm.subject?.trim() || !replayForm.text?.trim()) {
      toast("error", "Sender, subject, and body are required");
      return;
    }

    replayMutation.mutate({
      sender: replayForm.sender.trim(),
      from_: replayForm.from_?.trim() || replayForm.sender.trim(),
      to: replayForm.to?.trim() || "",
      subject: replayForm.subject.trim(),
      text: replayForm.text.trim(),
      html: replayForm.html?.trim() || "",
    });
  };

  const heroMetrics = [
    {
      label: "Processed",
      value: String(logs?.length ?? 0),
      hint: "Emails parsed into structured signals.",
      accent: "text-[var(--color-accent-primary)]",
    },
    {
      label: "Actionable",
      value: String(actionableLogs.length),
      hint: "Logs with a detected outcome or workflow step.",
      accent: "text-[var(--color-accent-success)]",
    },
    {
      label: "Avg confidence",
      value: avgConfidence,
      hint: "Model confidence across the recent signal window.",
      accent: "text-[var(--color-accent-warning)]",
    },
  ];

  return (
    <div className="space-y-6 px-4 py-4 sm:px-6 lg:px-8">
      <PageHeader
        eyebrow="Execute"
        title="Email Signals"
        description="A signal desk for recruiter and hiring-team communication. The page treats the inbox as an operational feed, not a mail client."
        meta={
          <>
            <span className="border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-tertiary)] px-3 py-2 font-mono text-[10px] font-bold uppercase tracking-[0.16em]">
              {logs?.length ?? 0} processed
            </span>
            <span className="border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-tertiary)] px-3 py-2 font-mono text-[10px] font-bold uppercase tracking-[0.16em]">
              {actionableLogs.length} actionable
            </span>
            <span className="border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-tertiary)] px-3 py-2 font-mono text-[10px] font-bold uppercase tracking-[0.16em]">
              {avgConfidence}
            </span>
          </>
        }
        actions={
          <Button variant="default" className={PRIMARY_BUTTON} onClick={submitReplay} disabled={replayMutation.isPending}>
            <ArrowClockwise size={16} weight="bold" />
            Process signal
          </Button>
        }
      />

      <MetricStrip
        items={heroMetrics.map((metric) => ({
          key: metric.label,
          label: metric.label,
          value: metric.value,
          hint: metric.hint,
          tone:
            metric.accent === "text-[var(--color-accent-success)]"
              ? "success"
              : metric.accent === "text-[var(--color-accent-warning)]"
                ? "warning"
                : "default",
        }))}
      />

      <div className="grid gap-6 xl:grid-cols-[minmax(340px,0.95fr)_minmax(0,1.05fr)]">
        <div className={`${PANEL} overflow-hidden`}>
          <div className="border-b-2 border-[var(--color-text-primary)] px-5 py-4">
            <div className="text-sm font-bold uppercase tracking-[0.2em]">Signal log</div>
            <div className="mt-4 grid gap-3 md:grid-cols-[minmax(0,1fr)_180px]">
              <Input
                value={searchValue}
                onChange={(event) => setSearchValue(event.target.value)}
                placeholder="Search sender, subject, company, or job title"
                icon={<MagnifyingGlass size={16} weight="bold" />}
                className={FIELD}
              />
              <Select
                value={actionFilter}
                onChange={(event) => setActionFilter(event.target.value)}
                options={FILTER_OPTIONS}
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
                    onClick={() => setSelectedLogId(log.id)}
                    className={cn(
                      "w-full border-2 px-4 py-4 text-left transition-transform duration-150",
                      selectedLogId === log.id
                        ? "border-[var(--color-text-primary)] bg-[var(--color-accent-primary-subtle)] shadow-[4px_4px_0px_0px_var(--color-accent-primary)]"
                        : "border-[var(--color-text-primary)] bg-[var(--color-bg-secondary)] shadow-[4px_4px_0px_0px_var(--color-text-primary)] hover:-translate-x-[2px] hover:-translate-y-[2px]"
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
                description="Adjust the action filter or search query to widen the log."
              />
            )}
          </div>
        </div>

        <div className="space-y-6">
          <div className={`${PANEL} p-5 sm:p-6`}>
            <div className="flex items-center gap-2 text-sm font-bold uppercase tracking-[0.18em]">
              <Funnel size={16} weight="bold" className="text-[var(--color-accent-primary)]" />
              Selected log detail
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
                      Detected action
                    </div>
                    <div className="mt-2 text-base font-bold">{selectedLog.parsed_action ?? "No structured action"}</div>
                    <div className="mt-2 text-sm text-[var(--color-text-secondary)]">
                      Confidence {selectedLog.confidence !== null ? `${Math.round(selectedLog.confidence * 100)}%` : "not available"}
                    </div>
                  </div>
                  <div className={`${PANEL_ALT} px-4 py-4`}>
                    <div className="text-[10px] font-bold uppercase tracking-[0.22em] text-[var(--color-text-muted)]">
                      Matched application
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
                  Processed {formatDistanceToNow(new Date(selectedLog.processed_at), { addSuffix: true })}.
                  Use this panel to verify classification before the signal gets folded into outcomes or
                  follow-up workflows.
                </div>
              </div>
            ) : (
              <EmptyState
                icon={<EnvelopeSimple size={32} weight="bold" />}
                title="Choose a log entry"
                description="Select a signal from the left to inspect company extraction, action parsing, and match confidence."
              />
            )}
          </div>

          <div className={`${PANEL} p-5 sm:p-6`}>
            <div className="flex items-center gap-2 text-sm font-bold uppercase tracking-[0.18em]">
              <Sparkle size={16} weight="bold" className="text-[var(--color-accent-warning)]" />
              Replay a signal
            </div>
            <p className="mt-1 text-sm leading-6 text-[var(--color-text-secondary)]">
              Manually send a webhook-shaped payload to test classification or backfill a missing signal.
            </p>
            <div className="mt-4 grid gap-4 md:grid-cols-2">
              <Input
                label="Sender"
                value={replayForm.sender ?? ""}
                onChange={(event) => setReplayForm((current) => ({ ...current, sender: event.target.value }))}
                placeholder="recruiter@company.com"
                className={FIELD}
              />
              <Input
                label="From"
                value={replayForm.from_ ?? ""}
                onChange={(event) => setReplayForm((current) => ({ ...current, from_: event.target.value }))}
                placeholder="Optional override"
                className={FIELD}
              />
            </div>
            <Input
              className={`${FIELD} mt-4`}
              label="Subject"
              value={replayForm.subject ?? ""}
              onChange={(event) => setReplayForm((current) => ({ ...current, subject: event.target.value }))}
              placeholder="Interview invitation for Senior Frontend Engineer"
            />
            <Textarea
              className={`${FIELD} mt-4 min-h-[160px]`}
              label="Body"
              value={replayForm.text ?? ""}
              onChange={(event) => setReplayForm((current) => ({ ...current, text: event.target.value }))}
              placeholder="Paste the inbound email body here."
            />
            <div className="mt-4 flex justify-end">
              <Button variant="default" className={PRIMARY_BUTTON} onClick={submitReplay} disabled={replayMutation.isPending}>
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
                  {replayResult.confidence !== null ? (
                    <span>Confidence: {Math.round(replayResult.confidence * 100)}%</span>
                  ) : null}
                </div>
              </div>
            ) : null}
          </div>

          <div className={`${PANEL_ALT} p-5 sm:p-6`}>
            <div className="flex items-center gap-2 text-sm font-bold uppercase tracking-[0.18em]">
              <CheckCircle size={16} weight="bold" className="text-[var(--color-accent-success)]" />
              Operating notes
            </div>
            <div className="mt-3 space-y-2 text-sm leading-6 text-[var(--color-text-secondary)]">
              <p>Use this page as the audit trail for inbound hiring communication, not as a general inbox.</p>
              <p>Unknown actions are still useful if the company and title extractions are correct.</p>
              <p>Replay is intentionally visible so missing automation does not block manual cleanup.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
