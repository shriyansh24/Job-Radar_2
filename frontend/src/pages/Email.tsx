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
import Badge from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import Card from "../components/ui/Card";
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

function MetricCard({
  label,
  value,
  hint,
}: {
  label: string;
  value: string;
  hint: string;
}) {
  return (
    <Card className="p-5">
      <div className="text-[11px] font-medium uppercase tracking-[0.18em] text-text-muted">{label}</div>
      <div className="mt-2 text-2xl font-semibold tracking-tight text-text-primary">{value}</div>
      <p className="mt-2 text-sm text-text-secondary">{hint}</p>
    </Card>
  );
}

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

  return (
    <div className="space-y-6">
      <Card className="overflow-hidden p-0">
        <div className="grid gap-5 border-b border-border bg-[linear-gradient(135deg,color-mix(in_srgb,var(--accent-primary)_10%,transparent),transparent_60%)] px-6 py-6 lg:grid-cols-[minmax(0,1.75fr)_minmax(0,1fr)]">
          <div>
            <div className="text-xs font-medium uppercase tracking-[0.18em] text-text-muted">Execute</div>
            <h1 className="mt-2 text-3xl font-semibold tracking-tight text-text-primary">Email Signals</h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-text-secondary">
              A signal desk for inbound recruiter and hiring-team communication. The structure leans on
              timeline logging rather than inbox chrome, so you can monitor outcomes instead of triaging mail.
            </p>
          </div>
          <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-1">
            <MetricCard
              label="Processed"
              value={String(logs?.length ?? 0)}
              hint="Emails parsed into structured signals."
            />
            <MetricCard
              label="Actionable"
              value={String(actionableLogs.length)}
              hint="Logs with a detected outcome or workflow step."
            />
            <MetricCard
              label="Avg Confidence"
              value={avgConfidence}
              hint="Model confidence across the recent signal window."
            />
          </div>
        </div>
      </Card>

      <div className="grid gap-6 xl:grid-cols-[minmax(340px,0.92fr)_minmax(0,1.28fr)]">
        <Card className="p-0">
          <div className="border-b border-border px-5 py-4">
            <div className="text-sm font-semibold text-text-primary">Signal log</div>
            <div className="mt-4 grid gap-3 md:grid-cols-[minmax(0,1fr)_180px]">
              <Input
                value={searchValue}
                onChange={(event) => setSearchValue(event.target.value)}
                placeholder="Search sender, subject, company, or job title"
                icon={<MagnifyingGlass size={16} weight="bold" />}
              />
              <Select
                value={actionFilter}
                onChange={(event) => setActionFilter(event.target.value)}
                options={FILTER_OPTIONS}
              />
            </div>
          </div>
          <div className="max-h-[760px] overflow-auto px-3 py-3">
            {isLoading ? (
              <div className="space-y-3 px-2 py-2">
                {Array.from({ length: 7 }).map((_, index) => (
                  <Skeleton key={index} variant="rect" className="h-24 w-full" />
                ))}
              </div>
            ) : filteredLogs.length ? (
              filteredLogs.map((log) => (
                <button
                  key={log.id}
                  type="button"
                  onClick={() => setSelectedLogId(log.id)}
                  className={cn(
                    "mb-2 w-full rounded-[var(--radius-xl)] border px-4 py-4 text-left transition-colors",
                    selectedLogId === log.id
                      ? "border-accent-primary/35 bg-accent-primary/8"
                      : "border-transparent bg-bg-secondary hover:border-border hover:bg-bg-tertiary"
                  )}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="truncate text-sm font-medium text-text-primary">{log.subject}</div>
                      <div className="mt-1 truncate text-sm text-text-secondary">{log.sender}</div>
                    </div>
                    <Badge variant={log.parsed_action ? "info" : "default"}>
                      {log.parsed_action ?? "unknown"}
                    </Badge>
                  </div>
                  <div className="mt-3 flex flex-wrap items-center gap-3 text-xs text-text-muted">
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
              ))
            ) : (
              <EmptyState
                icon={<EnvelopeSimple size={32} weight="bold" />}
                title="No matching signals"
                description="Adjust the action filter or search query to widen the log."
              />
            )}
          </div>
        </Card>

        <div className="space-y-6">
          <Card className="p-5">
            <div className="flex items-center gap-2 text-sm font-semibold text-text-primary">
              <Funnel size={16} weight="bold" className="text-accent-primary" />
              Selected log detail
            </div>
            {selectedLog ? (
              <div className="mt-4 space-y-4">
                <div className="rounded-[var(--radius-xl)] border border-border bg-bg-secondary px-4 py-4">
                  <div className="text-lg font-semibold tracking-tight text-text-primary">{selectedLog.subject}</div>
                  <div className="mt-2 text-sm text-text-secondary">{selectedLog.sender}</div>
                </div>

                <div className="grid gap-4 md:grid-cols-2">
                  <div className="rounded-[var(--radius-xl)] border border-border bg-bg-secondary px-4 py-4">
                    <div className="text-[11px] font-medium uppercase tracking-[0.18em] text-text-muted">Detected action</div>
                    <div className="mt-2 text-base font-medium text-text-primary">
                      {selectedLog.parsed_action ?? "No structured action"}
                    </div>
                    <div className="mt-2 text-sm text-text-secondary">
                      Confidence {selectedLog.confidence !== null ? `${Math.round(selectedLog.confidence * 100)}%` : "not available"}
                    </div>
                  </div>
                  <div className="rounded-[var(--radius-xl)] border border-border bg-bg-secondary px-4 py-4">
                    <div className="text-[11px] font-medium uppercase tracking-[0.18em] text-text-muted">Matched application</div>
                    <div className="mt-2 break-all text-sm text-text-primary">
                      {selectedLog.matched_application_id ?? "No application match"}
                    </div>
                  </div>
                </div>

                <div className="grid gap-4 md:grid-cols-2">
                  <div className="rounded-[var(--radius-xl)] border border-border bg-bg-secondary px-4 py-4">
                    <div className="text-[11px] font-medium uppercase tracking-[0.18em] text-text-muted">Company</div>
                    <div className="mt-2 text-sm text-text-primary">{selectedLog.company_extracted ?? "Unknown"}</div>
                  </div>
                  <div className="rounded-[var(--radius-xl)] border border-border bg-bg-secondary px-4 py-4">
                    <div className="text-[11px] font-medium uppercase tracking-[0.18em] text-text-muted">Job title</div>
                    <div className="mt-2 text-sm text-text-primary">{selectedLog.job_title_extracted ?? "Unknown"}</div>
                  </div>
                </div>

                <div className="rounded-[var(--radius-xl)] border border-border bg-bg-secondary px-4 py-4 text-sm leading-6 text-text-secondary">
                  Processed {formatDistanceToNow(new Date(selectedLog.processed_at), { addSuffix: true })}.
                  Use this panel to verify classification before the signal gets folded into outcomes or follow-up workflows.
                </div>
              </div>
            ) : (
              <EmptyState
                icon={<EnvelopeSimple size={32} weight="bold" />}
                title="Choose a log entry"
                description="Select a signal from the left to inspect company extraction, action parsing, and match confidence."
              />
            )}
          </Card>

          <Card className="p-5">
            <div className="flex items-center gap-2 text-sm font-semibold text-text-primary">
              <Sparkle size={16} weight="bold" className="text-accent-warning" />
              Replay a signal
            </div>
            <p className="mt-1 text-sm text-text-secondary">
              Manually send a webhook-shaped payload to test classification or backfill a missing signal.
            </p>
            <div className="mt-4 grid gap-4 md:grid-cols-2">
              <Input
                label="Sender"
                value={replayForm.sender ?? ""}
                onChange={(event) => setReplayForm((current) => ({ ...current, sender: event.target.value }))}
                placeholder="recruiter@company.com"
              />
              <Input
                label="From"
                value={replayForm.from_ ?? ""}
                onChange={(event) => setReplayForm((current) => ({ ...current, from_: event.target.value }))}
                placeholder="Optional override"
              />
            </div>
            <Input
              className="mt-4"
              label="Subject"
              value={replayForm.subject ?? ""}
              onChange={(event) => setReplayForm((current) => ({ ...current, subject: event.target.value }))}
              placeholder="Interview invitation for Senior Frontend Engineer"
            />
            <Textarea
              className="mt-4 min-h-[160px]"
              label="Body"
              value={replayForm.text ?? ""}
              onChange={(event) => setReplayForm((current) => ({ ...current, text: event.target.value }))}
              placeholder="Paste the inbound email body here."
            />
            <div className="mt-4 flex justify-end">
              <Button variant="default" onClick={submitReplay} disabled={replayMutation.isPending}>
                <ArrowClockwise size={16} weight="bold" />
                Process signal
              </Button>
            </div>

            {replayResult ? (
              <div className="mt-4 rounded-[var(--radius-xl)] border border-border bg-bg-secondary px-4 py-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="text-sm font-medium text-text-primary">{replayResult.status}</div>
                    <p className="mt-1 text-sm text-text-secondary">{replayResult.message ?? "Signal processed."}</p>
                  </div>
                  <Badge variant={replayResult.status === "updated" ? "success" : "info"}>
                    {replayResult.action ?? "no action"}
                  </Badge>
                </div>
                <div className="mt-3 flex flex-wrap gap-3 text-xs text-text-muted">
                  {replayResult.company ? <span>Company: {replayResult.company}</span> : null}
                  {replayResult.application_id ? <span>Application: {replayResult.application_id}</span> : null}
                  {replayResult.confidence !== null ? (
                    <span>Confidence: {Math.round(replayResult.confidence * 100)}%</span>
                  ) : null}
                </div>
              </div>
            ) : null}
          </Card>

          <Card className="p-5">
            <div className="flex items-center gap-2 text-sm font-semibold text-text-primary">
              <CheckCircle size={16} weight="bold" className="text-accent-success" />
              Operating notes
            </div>
            <div className="mt-3 space-y-2 text-sm leading-6 text-text-secondary">
              <p>Use this page as the audit trail for inbound hiring communication, not as a general inbox.</p>
              <p>Unknown actions are still useful if the company and title extractions are correct.</p>
              <p>Replay is intentionally visible so missing automation does not block manual cleanup.</p>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
