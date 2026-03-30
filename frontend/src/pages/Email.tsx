import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useDeferredValue, useEffect, useState } from "react";
import { emailApi, type EmailWebhookPayload, type EmailWebhookResponse } from "../api/email";
import { MetricStrip } from "../components/system/MetricStrip";
import { PageHeader } from "../components/system/PageHeader";
import { SplitWorkspace } from "../components/system/SplitWorkspace";
import { StateBlock } from "../components/system/StateBlock";
import { EmailNotesPanel, EmailReplayPanel, EmailSignalDetail, EmailSignalList } from "../components/email/EmailPanels";
import { toast } from "../components/ui/toastService";

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
    { label: "Processed", value: String(logs?.length ?? 0), hint: "Parsed signals." },
    { label: "Actionable", value: String(actionableLogs.length), hint: "Known outcomes." },
    { label: "Avg confidence", value: avgConfidence, hint: "Signal confidence." },
  ];

  return (
    <div className="space-y-6 px-4 py-4 sm:px-6 lg:px-8">
      <PageHeader
        eyebrow="Execute"
        title="Email Signals"
        description="Inspect inbox signals, replay payloads, and keep the audit trail tight."
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
      />

      <MetricStrip
        items={heroMetrics.map((metric) => ({
          key: metric.label,
          label: metric.label,
          value: metric.value,
          hint: metric.hint,
          tone: metric.label === "Actionable" ? "success" : metric.label === "Avg confidence" ? "warning" : "default",
        }))}
      />

      <SplitWorkspace
        primary={
          <EmailSignalList
            isLoading={isLoading}
            filteredLogs={filteredLogs}
            selectedLogId={selectedLogId}
            searchValue={searchValue}
            actionFilter={actionFilter}
            filterOptions={FILTER_OPTIONS}
            onSearchChange={setSearchValue}
            onActionFilterChange={setActionFilter}
            onSelect={setSelectedLogId}
          />
        }
        secondary={
          <div className="space-y-6">
            <EmailSignalDetail selectedLog={selectedLog} />
            <EmailReplayPanel
              replayForm={replayForm}
              replayResult={replayResult}
              pending={replayMutation.isPending}
              onChange={setReplayForm}
              onSubmit={submitReplay}
            />
            <EmailNotesPanel />
          </div>
        }
      />

      <StateBlock
        tone="neutral"
        title="Scope"
        description="This page is for inbound hiring signals only. General inbox features stay out of the way."
      />
    </div>
  );
}
