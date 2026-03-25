import {
  ArrowClockwise,
  CaretLeft,
  CaretRight,
  CheckCircle,
  Crosshair,
  Lightning,
  LinkSimple,
  LockOpen,
  UploadSimple,
  Warning,
  XCircle,
} from "@phosphor-icons/react";
import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { formatDistanceToNow } from "date-fns";
import { useRef, useState, type ChangeEvent } from "react";
import {
  scraperApi,
  type ScrapeAttempt,
  type ScrapeTarget,
  type TargetListParams,
} from "../api/scraper";
import { MetricStrip } from "../components/system/MetricStrip";
import { PageHeader } from "../components/system/PageHeader";
import { StateBlock } from "../components/system/StateBlock";
import { Surface } from "../components/system/Surface";
import Badge from "../components/ui/Badge";
import Button from "../components/ui/Button";
import EmptyState from "../components/ui/EmptyState";
import Modal from "../components/ui/Modal";
import Select from "../components/ui/Select";
import Skeleton from "../components/ui/Skeleton";
import Textarea from "../components/ui/Textarea";
import Toggle from "../components/ui/Toggle";
import { toast } from "../components/ui/toastService";
import { cn, getSafeExternalUrl } from "../lib/utils";

// ---------- helpers ----------

function relativeTime(dateStr: string | null): string {
  if (!dateStr) return "never";
  try {
    return formatDistanceToNow(new Date(dateStr), { addSuffix: true });
  } catch {
    return "unknown";
  }
}

function priorityVariant(
  pc: string
): "warning" | "danger" | "info" | "default" {
  switch (pc) {
    case "watchlist":
      return "warning";
    case "hot":
      return "danger";
    case "warm":
      return "info";
    default:
      return "default";
  }
}

function atsVariant(vendor: string | null): "success" | "default" {
  if (!vendor || vendor === "unknown") return "default";
  return "success";
}

function attemptStatusIcon(status: string) {
  if (status === "success")
    return <CheckCircle size={14} weight="fill" className="text-accent-success" />;
  if (status === "failure" || status === "error")
    return <XCircle size={14} weight="fill" className="text-accent-danger" />;
  return <ArrowClockwise size={14} weight="bold" className="text-text-muted" />;
}

// ---------- sub-components ----------

function TargetRowSkeleton() {
  return (
    <div className="grid gap-3 border-b-2 border-border px-5 py-4 md:grid-cols-[minmax(0,1.5fr)_140px_140px_150px]">
      <div className="space-y-2">
        <Skeleton variant="text" className="h-4 w-1/3" />
        <Skeleton variant="text" className="h-3 w-2/3" />
      </div>
      <Skeleton variant="text" className="h-4 w-16" />
      <Skeleton variant="text" className="h-4 w-16" />
      <Skeleton variant="text" className="h-4 w-12" />
    </div>
  );
}

function AttemptTimeline({ attempts }: { attempts: ScrapeAttempt[] }) {
  if (!attempts.length) {
    return (
      <p className="text-xs text-text-muted italic">No attempts recorded yet.</p>
    );
  }
  return (
    <div className="space-y-2">
      {attempts.slice(0, 5).map((a) => (
        <div
          key={a.id}
          className="flex items-start gap-3 border-2 border-border bg-[var(--color-bg-tertiary)] px-4 py-3"
        >
          <div className="mt-0.5">{attemptStatusIcon(a.status)}</div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-mono text-[11px] font-bold uppercase tracking-[0.16em] text-text-primary">
                Tier {a.actual_tier_used}
              </span>
              <span
                className={cn(
                  "font-mono text-[11px] font-bold uppercase tracking-[0.16em]",
                  a.status === "success"
                    ? "text-accent-success"
                    : "text-accent-danger"
                )}
              >
                {a.status}
              </span>
              <span className="text-xs text-text-muted">
                {a.jobs_extracted} job{a.jobs_extracted !== 1 ? "s" : ""}
              </span>
              {a.duration_ms != null && (
                <span className="text-xs text-text-muted">
                  {(a.duration_ms / 1000).toFixed(1)}s
                </span>
              )}
            </div>
            {a.error_message && (
              <p className="text-xs text-accent-danger mt-0.5 truncate" title={a.error_message}>
                {a.error_message}
              </p>
            )}
            <p className="text-xs text-text-muted mt-0.5">
              {relativeTime(a.created_at)}
            </p>
          </div>
        </div>
      ))}
    </div>
  );
}

function TargetDetail({
  targetId,
  onClose,
}: {
  targetId: string;
  onClose: () => void;
}) {
  const queryClient = useQueryClient();

  const { data: target, isLoading } = useQuery({
    queryKey: ["target", targetId],
    queryFn: () => scraperApi.getTarget(targetId).then((r) => r.data),
    enabled: !!targetId,
  });
  const safeTargetUrl = getSafeExternalUrl(target?.url);

  const triggerMutation = useMutation({
    mutationFn: (id: string) => scraperApi.triggerTarget(id),
    onSuccess: () => {
      toast("success", "Target triggered successfully");
      queryClient.invalidateQueries({ queryKey: ["targets"] });
      queryClient.invalidateQueries({ queryKey: ["target", targetId] });
    },
    onError: () => toast("error", "Failed to trigger target"),
  });

  const releaseMutation = useMutation({
    mutationFn: (id: string) => scraperApi.releaseTarget(id),
    onSuccess: () => {
      toast("success", "Target released from quarantine");
      queryClient.invalidateQueries({ queryKey: ["targets"] });
      queryClient.invalidateQueries({ queryKey: ["target", targetId] });
    },
    onError: () => toast("error", "Failed to release target"),
  });

  const toggleMutation = useMutation({
    mutationFn: ({ id, enabled }: { id: string; enabled: boolean }) =>
      scraperApi.updateTarget(id, { enabled }),
    onSuccess: (_, vars) => {
      toast("success", vars.enabled ? "Target enabled" : "Target disabled");
      queryClient.invalidateQueries({ queryKey: ["targets"] });
      queryClient.invalidateQueries({ queryKey: ["target", targetId] });
    },
    onError: () => toast("error", "Failed to update target"),
  });

  return (
    <div className="flex flex-col h-full">
      {/* Detail header */}
      <div className="flex items-center justify-between border-b-2 border-border bg-[var(--color-bg-tertiary)] px-5 py-4 shrink-0">
        <div>
          <div className="font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-text-muted">
            Target Detail
          </div>
          <div className="mt-2 max-w-xs truncate text-xl font-black uppercase tracking-[-0.05em] text-text-primary">
            {isLoading ? (
              <Skeleton variant="text" className="w-32 h-4" />
            ) : (
              target?.company_name ?? target?.url ?? "-"
            )}
          </div>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="hard-press border-2 border-border bg-card p-2 text-text-muted shadow-[var(--shadow-xs)] hover:text-text-primary"
          aria-label="Close detail panel"
        >
          <CaretRight size={16} weight="bold" />
        </button>
      </div>

      {isLoading ? (
        <div className="p-5 space-y-4">
          <Skeleton variant="text" className="w-3/4 h-5" />
          <Skeleton variant="text" className="w-1/2 h-4" />
          <Skeleton variant="rect" className="w-full h-28" />
          <Skeleton variant="rect" className="w-full h-28" />
        </div>
      ) : !target ? null : (
        <div className="flex-1 overflow-auto p-5 space-y-5">
          {/* Status badges row */}
          <div className="flex flex-wrap gap-2">
            <Badge variant={priorityVariant(target.priority_class)}>
              {target.priority_class}
            </Badge>
            <Badge variant={atsVariant(target.ats_vendor)}>
              {target.ats_vendor ?? "unknown"}
            </Badge>
            {target.quarantined && (
              <Badge variant="danger">quarantined</Badge>
            )}
            {!target.enabled && (
              <Badge variant="default">disabled</Badge>
            )}
          </div>

          {/* URL */}
          <div className="space-y-1">
            <p className="text-xs font-medium text-text-muted uppercase tracking-wide">
              URL
            </p>
            {safeTargetUrl ? (
              <a
                href={safeTargetUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-accent-primary hover:underline break-all flex items-start gap-1"
              >
                <LinkSimple size={14} className="mt-0.5 shrink-0" />
                {safeTargetUrl}
              </a>
            ) : (
              <span className="text-sm text-text-secondary break-all">{target.url}</span>
            )}
          </div>

          {/* Stats grid */}
          <div className="grid grid-cols-2 gap-3">
            {[
              { label: "Source Kind", value: target.source_kind },
              {
                label: "ATS Board Token",
                value: target.ats_board_token ?? "-",
              },
              {
                label: "Schedule Interval",
                value: `${target.schedule_interval_m}m`,
              },
              {
                label: "Tiers",
                value: `${target.start_tier} to ${target.max_tier}`,
              },
              {
                label: "Last Success",
                value: relativeTime(target.last_success_at),
              },
              {
                label: "Last Failure",
                value: relativeTime(target.last_failure_at),
              },
              {
                label: "Consecutive Failures",
                value: String(target.consecutive_failures),
              },
              {
                label: "Total Failures",
                value: String(target.failure_count),
              },
              {
                label: "Last HTTP Status",
                value: target.last_http_status != null
                  ? String(target.last_http_status)
                  : "-",
              },
              {
                label: "Next Scheduled",
                value: relativeTime(target.next_scheduled_at),
              },
            ].map(({ label, value }) => (
              <div key={label} className="border-2 border-border bg-[var(--color-bg-tertiary)] px-4 py-3">
                <p className="font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-text-muted">
                  {label}
                </p>
                <p className="mt-3 truncate text-sm text-text-primary">
                  {value}
                </p>
              </div>
            ))}
          </div>

          {/* Quarantine reason */}
          {target.quarantined && target.quarantine_reason && (
            <div className="flex items-start gap-3 border-2 border-[var(--color-accent-danger)] bg-[var(--color-accent-danger-subtle)] px-4 py-4">
              <Warning
                size={16}
                weight="fill"
                className="text-accent-danger shrink-0 mt-0.5"
              />
              <div>
                <p className="font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-accent-danger">
                  Quarantine Reason
                </p>
                <p className="mt-2 text-sm text-text-secondary">
                  {target.quarantine_reason}
                </p>
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="space-y-2">
            <p className="text-xs font-medium text-text-muted uppercase tracking-wide">
              Actions
            </p>
            <div className="flex flex-wrap gap-2">
              <Button
                variant="primary"
                size="sm"
                loading={triggerMutation.isPending}
                onClick={() => triggerMutation.mutate(target.id)}
                icon={<Lightning size={14} weight="bold" />}
              >
                Trigger Now
              </Button>
              {target.quarantined && (
                <Button
                  variant="secondary"
                  size="sm"
                  loading={releaseMutation.isPending}
                  onClick={() => releaseMutation.mutate(target.id)}
                  icon={<LockOpen size={14} weight="bold" />}
                >
                  Release
                </Button>
              )}
            </div>
            <div className="flex items-center gap-3 pt-1">
              <Toggle
                checked={target.enabled}
                onChange={(checked) =>
                  toggleMutation.mutate({ id: target.id, enabled: checked })
                }
                disabled={toggleMutation.isPending}
              />
              <span className="text-sm text-text-secondary">
                {target.enabled ? "Enabled" : "Disabled"}
              </span>
            </div>
          </div>

          {/* Recent attempts */}
          <div className="space-y-2">
            <p className="text-xs font-medium text-text-muted uppercase tracking-wide">
              Recent Attempts
            </p>
            <AttemptTimeline attempts={target.recent_attempts ?? []} />
          </div>

          {/* Meta */}
          <div className="text-xs text-text-muted space-y-0.5 pt-2 border-t border-border/50">
            <p>Created {relativeTime(target.created_at)}</p>
            <p>Updated {relativeTime(target.updated_at)}</p>
          </div>
        </div>
      )}
    </div>
  );
}

// ---------- Import modal ----------

interface ImportEntry {
  url: string;
  company_name?: string;
}

function normalizeImportEntries(entries: ImportEntry[]) {
  const normalized: ImportEntry[] = [];

  for (const entry of entries) {
    const safeUrl = getSafeExternalUrl(entry.url);
    if (!safeUrl) {
      return {
        entries: [] as ImportEntry[],
        error: 'Each entry must have a valid "http://" or "https://" URL',
      };
    }

    normalized.push({
      ...entry,
      url: safeUrl,
    });
  }

  return { entries: normalized, error: null as string | null };
}

function ImportModal({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [jsonText, setJsonText] = useState("");
  const [preview, setPreview] = useState<ImportEntry[] | null>(null);
  const [parseError, setParseError] = useState<string | null>(null);

  const importMutation = useMutation({
    mutationFn: (targets: ImportEntry[]) =>
      scraperApi.importTargets(targets).then((r) => r.data),
    onSuccess: (result) => {
      toast(
        "success",
        `Imported ${result.imported}, skipped ${result.skipped}${result.errors.length ? `, ${result.errors.length} errors` : ""}`
      );
      queryClient.invalidateQueries({ queryKey: ["targets"] });
      onClose();
      setJsonText("");
      setPreview(null);
    },
    onError: () => toast("error", "Import failed"),
  });

  const handleParse = () => {
    setParseError(null);
    try {
      const parsed = JSON.parse(jsonText.trim());
      if (!Array.isArray(parsed)) {
        setParseError("Expected a JSON array");
        setPreview(null);
        return;
      }
      const entries = parsed as ImportEntry[];
      if (entries.some((e) => !e.url)) {
        setParseError('Each entry must have a "url" field');
        setPreview(null);
        return;
      }
      const { entries: normalizedEntries, error } = normalizeImportEntries(entries);
      if (error) {
        setParseError(error);
        setPreview(null);
        return;
      }
      setPreview(normalizedEntries);
    } catch (err) {
      setParseError(`Invalid JSON: ${(err as Error).message}`);
      setPreview(null);
    }
  };

  const handleFileUpload = async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      const text = await file.text();
      if (file.name.endsWith(".csv")) {
        // Simple CSV parse: header row then data rows
        const lines = text.trim().split("\n");
        const headers = lines[0].split(",").map((h) => h.trim().replace(/^"|"$/g, ""));
        const urlIdx = headers.findIndex((h) => h.toLowerCase() === "url");
        const nameIdx = headers.findIndex(
          (h) => h.toLowerCase() === "company_name" || h.toLowerCase() === "company"
        );
        if (urlIdx === -1) {
          setParseError('CSV must have a "url" column');
          return;
        }
        const entries: ImportEntry[] = lines.slice(1).map((line) => {
          const cols = line.split(",").map((c) => c.trim().replace(/^"|"$/g, ""));
          return {
            url: cols[urlIdx] ?? "",
            ...(nameIdx !== -1 ? { company_name: cols[nameIdx] } : {}),
          };
        });
        const { entries: normalizedEntries, error } = normalizeImportEntries(entries);
        if (error) {
          setParseError(error);
          setPreview(null);
          return;
        }
        setJsonText(JSON.stringify(normalizedEntries, null, 2));
        setPreview(normalizedEntries);
      } else {
        setJsonText(text);
        setParseError(null);
        setPreview(null);
      }
    } catch {
      setParseError("Failed to read file");
    }
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const handleClose = () => {
    onClose();
    setJsonText("");
    setPreview(null);
    setParseError(null);
  };

  return (
    <Modal open={open} onClose={handleClose} title="Import Targets" size="lg">
      <div className="space-y-4">
        <div className="flex items-center gap-3">
          <p className="text-sm text-text-secondary flex-1">
            Paste a JSON array of{" "}
            <code className="font-mono text-xs bg-bg-tertiary px-1 py-0.5 rounded">
              {"[{url, company_name}]"}
            </code>{" "}
            or upload a CSV / JSON file.
          </p>
          <input
            ref={fileInputRef}
            type="file"
            accept=".json,.csv"
            onChange={handleFileUpload}
            className="hidden"
          />
          <Button
            variant="secondary"
            size="sm"
            onClick={() => fileInputRef.current?.click()}
            icon={<UploadSimple size={14} weight="bold" />}
          >
            Upload File
          </Button>
        </div>

        <Textarea
          label="JSON Array"
          placeholder='[{"url": "https://...", "company_name": "Acme"}]'
          value={jsonText}
          onChange={(e) => {
            setJsonText(e.target.value);
            setPreview(null);
            setParseError(null);
          }}
          rows={8}
          className="font-mono text-xs"
        />

        {parseError && (
          <p className="text-xs text-accent-danger flex items-center gap-1">
            <Warning size={14} weight="fill" />
            {parseError}
          </p>
        )}

        {!preview && (
          <Button variant="secondary" size="sm" onClick={handleParse} disabled={!jsonText.trim()}>
            Preview
          </Button>
        )}

        {preview && (
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <CheckCircle size={16} weight="fill" className="text-accent-success" />
              <p className="text-sm font-medium text-text-primary">
                {preview.length} target{preview.length !== 1 ? "s" : ""} ready to import
              </p>
            </div>
            <div className="overflow-hidden border-2 border-border">
              <table className="w-full text-xs">
                <thead>
                  <tr className="bg-[var(--color-bg-tertiary)] text-text-muted">
                    <th className="px-3 py-2 text-left font-medium">URL</th>
                    <th className="px-3 py-2 text-left font-medium">Company</th>
                  </tr>
                </thead>
                <tbody>
                  {preview.slice(0, 5).map((e, i) => (
                    <tr key={i} className="border-t-2 border-border">
                      <td className="px-3 py-2 text-text-secondary truncate max-w-[200px]">
                        {e.url}
                      </td>
                      <td className="px-3 py-2 text-text-secondary">
                        {e.company_name ?? "-"}
                      </td>
                    </tr>
                  ))}
                  {preview.length > 5 && (
                    <tr className="border-t-2 border-border">
                      <td
                        colSpan={2}
                        className="px-3 py-2 text-center text-text-muted"
                      >
                        ...and {preview.length - 5} more
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        <div className="flex justify-end gap-2 pt-2">
          <Button variant="secondary" onClick={handleClose}>
            Cancel
          </Button>
          <Button
            variant="primary"
            disabled={!preview || importMutation.isPending}
            loading={importMutation.isPending}
            onClick={() => preview && importMutation.mutate(preview)}
          >
            Import {preview ? `${preview.length} Targets` : ""}
          </Button>
        </div>
      </div>
    </Modal>
  );
}

// ---------- Main target row ----------

function TargetRow({
  target,
  isSelected,
  onClick,
  onToggleEnabled,
}: {
  target: ScrapeTarget;
  isSelected: boolean;
  onClick: () => void;
  onToggleEnabled: (enabled: boolean) => void;
}) {
  const rowBg = target.quarantined
    ? "bg-accent-danger/5 hover:bg-accent-danger/10 border-l-4 border-l-accent-danger"
    : isSelected
    ? "bg-bg-tertiary"
    : "hover:bg-bg-tertiary/60";

  return (
    <div
      role="button"
      tabIndex={0}
      className={cn(
        "grid cursor-pointer gap-3 border-b-2 border-border px-5 py-4 transition-colors md:grid-cols-[minmax(0,1.5fr)_140px_140px_150px] md:items-start",
        rowBg
      )}
      onClick={onClick}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          onClick();
        }
      }}
    >
      <div className="min-w-0">
        <p className="truncate text-lg font-black uppercase tracking-[-0.05em] text-text-primary">
          {target.company_name ?? "-"}
        </p>
        <p className="mt-2 truncate text-sm text-text-muted">{target.url}</p>
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <Badge variant={priorityVariant(target.priority_class)} size="sm">
            {target.priority_class}
          </Badge>
          <Badge variant={atsVariant(target.ats_vendor)} size="sm">
            {target.ats_vendor ?? "unknown"}
          </Badge>
          {target.quarantined && (
            <Badge variant="danger" size="sm">
              quarantined
            </Badge>
          )}
          {target.consecutive_failures > 0 && (
            <span className="font-mono text-xs text-accent-danger">
              {target.consecutive_failures}x fail
            </span>
          )}
        </div>
      </div>
      <div>
        <p className="font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-text-muted md:hidden">
          Source Kind
        </p>
        <p className="text-sm text-text-secondary">Source: {target.source_kind}</p>
      </div>
      <div>
        <p className="font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-text-muted md:hidden">
          Last Success
        </p>
        <p className="text-sm text-text-secondary">{relativeTime(target.last_success_at)}</p>
      </div>
      <div className="flex items-center justify-between gap-3 md:justify-end">
        <p className="font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-text-muted md:hidden">
          Enabled
        </p>
        <div onClick={(e) => e.stopPropagation()}>
          <Toggle checked={target.enabled} onChange={onToggleEnabled} />
        </div>
      </div>
    </div>
  );
}

// ---------- Page ----------

export default function Targets() {
  const queryClient = useQueryClient();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [showImport, setShowImport] = useState(false);
  const [page, setPage] = useState(0);
  const pageSize = 50;
  // removed unused listRef — using window.scrollTo instead

  const [filters, setFilters] = useState<{
    priority_class: string;
    ats_vendor: string;
    status: string;
  }>({
    priority_class: "",
    ats_vendor: "",
    status: "",
  });

  // Build API params
  const apiParams: TargetListParams = {
    limit: pageSize,
    offset: page * pageSize,
  };
  if (filters.priority_class) apiParams.priority_class = filters.priority_class;
  if (filters.ats_vendor) apiParams.ats_vendor = filters.ats_vendor;
  if (filters.status === "enabled") apiParams.enabled = true;
  if (filters.status === "disabled") apiParams.enabled = false;
  if (filters.status === "quarantined") apiParams.quarantined = true;

  const { data: targets, isLoading, isError } = useQuery({
    queryKey: ["targets", apiParams],
    queryFn: () => scraperApi.listTargets(apiParams).then((r) => r.data),
    placeholderData: keepPreviousData, // Keep old page data visible while new page loads
  });

  const batchMutation = useMutation({
    mutationFn: () => scraperApi.triggerBatch(),
    onSuccess: (res) => {
      toast(
        "success",
        `Batch triggered - ${res.data.jobs_found} jobs found`
      );
      queryClient.invalidateQueries({ queryKey: ["targets"] });
    },
    onError: () => toast("error", "Batch trigger failed"),
  });

  const toggleEnabledMutation = useMutation({
    mutationFn: ({ id, enabled }: { id: string; enabled: boolean }) =>
      scraperApi.updateTarget(id, { enabled }),
    onSuccess: (_, vars) => {
      toast("success", vars.enabled ? "Target enabled" : "Target disabled");
      queryClient.invalidateQueries({ queryKey: ["targets"] });
      if (selectedId) queryClient.invalidateQueries({ queryKey: ["target", selectedId] });
    },
    onError: () => toast("error", "Failed to update target"),
  });

  const list = targets?.items ?? [];
  const totalCount = targets?.total ?? 0;
  const hasMore = list.length === pageSize;
  const enabledCount = list.filter((target) => target.enabled).length;
  const quarantinedCount = list.filter((target) => target.quarantined).length;
  const vendors = new Set(list.map((target) => target.ats_vendor || "unknown"));

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Operations"
        title="Scrape Targets"
        description="A responsive operator view for target ingestion, quarantine state, and batch scraper control. The list stays dense on desktop and collapses into a stacked detail flow on phone and tablet."
        actions={
          <>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setShowImport(true)}
              icon={<UploadSimple size={14} weight="bold" />}
            >
              Import Targets
            </Button>
            <Button
              variant="primary"
              size="sm"
              loading={batchMutation.isPending}
              onClick={() => batchMutation.mutate()}
              icon={<Lightning size={14} weight="bold" />}
            >
              Trigger Batch
            </Button>
          </>
        }
        meta={
          !isLoading ? (
            <div className="font-mono font-bold uppercase tracking-[0.18em]">
              {totalCount} total targets
            </div>
          ) : null
        }
      />

      <MetricStrip
        items={[
          {
            key: "visible",
            label: "Visible targets",
            value: list.length.toLocaleString(),
            hint: "Rows in the current filtered page window.",
            icon: <Crosshair size={18} weight="bold" />,
          },
          {
            key: "enabled",
            label: "Enabled",
            value: enabledCount.toLocaleString(),
            hint: "Targets still eligible to run on the current page.",
            icon: <CheckCircle size={18} weight="bold" />,
            tone: "success",
          },
          {
            key: "quarantined",
            label: "Quarantined",
            value: quarantinedCount.toLocaleString(),
            hint: "Targets blocked pending review or release.",
            icon: <Warning size={18} weight="bold" />,
            tone: quarantinedCount ? "warning" : "default",
          },
          {
            key: "vendors",
            label: "ATS vendors",
            value: vendors.size.toLocaleString(),
            hint: "Unique ATS vendors represented in the current result set.",
            icon: <ArrowClockwise size={18} weight="bold" />,
          },
        ]}
      />

      <Surface tone="default" padding="lg" radius="xl">
        <div className="grid gap-4 md:grid-cols-3">
          <Select
            value={filters.priority_class}
            onChange={(e) => {
              setFilters((f) => ({ ...f, priority_class: e.target.value }));
              setPage(0);
            }}
            options={[
              { value: "watchlist", label: "Watchlist" },
              { value: "hot", label: "Hot" },
              { value: "warm", label: "Warm" },
              { value: "cool", label: "Cool" },
            ]}
            placeholder="All priorities"
            label="Priority"
          />
          <Select
            value={filters.ats_vendor}
            onChange={(e) => {
              setFilters((f) => ({ ...f, ats_vendor: e.target.value }));
              setPage(0);
            }}
            options={[
              { value: "greenhouse", label: "Greenhouse" },
              { value: "lever", label: "Lever" },
              { value: "ashby", label: "Ashby" },
              { value: "workday", label: "Workday" },
              { value: "unknown", label: "Unknown" },
            ]}
            placeholder="All vendors"
            label="ATS vendor"
          />
          <Select
            value={filters.status}
            onChange={(e) => {
              setFilters((f) => ({ ...f, status: e.target.value }));
              setPage(0);
            }}
            options={[
              { value: "enabled", label: "Enabled" },
              { value: "disabled", label: "Disabled" },
              { value: "quarantined", label: "Quarantined" },
            ]}
            placeholder="All statuses"
            label="Status"
          />
        </div>
      </Surface>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.08fr)_minmax(360px,0.92fr)]">
        <Surface tone="default" padding="none" radius="xl" className="overflow-hidden">
          <div className="border-b-2 border-border px-5 py-4">
            <div className="flex items-baseline justify-between gap-3">
              <div>
                <div className="text-sm font-black uppercase tracking-[-0.03em] text-text-primary">Targets</div>
                <div className="mt-1 text-sm text-muted-foreground">
                  <span className="font-mono text-text-secondary">{list.length}</span> of {totalCount} shown
                </div>
              </div>
              <div className="font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
                Page {page + 1}
              </div>
            </div>
          </div>

          <div className="min-h-[420px]">
            {isError ? (
              <div className="p-8 text-center text-sm text-accent-danger">
                Failed to load targets. Please try again.
              </div>
            ) : isLoading ? (
              Array.from({ length: 10 }).map((_, i) => <TargetRowSkeleton key={i} />)
            ) : list.length === 0 ? (
              <div className="p-6">
                <EmptyState
                  icon={<Crosshair size={40} weight="bold" />}
                  title="No targets found"
                  description="Import targets or adjust your filters"
                  action={{ label: "Import Targets", onClick: () => setShowImport(true) }}
                />
              </div>
            ) : (
              list.map((target) => (
                <TargetRow
                  key={target.id}
                  target={target}
                  isSelected={target.id === selectedId}
                  onClick={() => setSelectedId(target.id === selectedId ? null : target.id)}
                  onToggleEnabled={(enabled) =>
                    toggleEnabledMutation.mutate({ id: target.id, enabled })
                  }
                />
              ))
            )}
          </div>

          <div className="flex items-center justify-between border-t-2 border-border px-5 py-3">
            <span className="text-xs text-text-muted">
              Page <span className="font-mono text-text-secondary">{page + 1}</span>
            </span>
            <div className="flex gap-1">
              <Button
                variant="ghost"
                size="sm"
                disabled={page === 0}
                onClick={() => {
                  setPage((p) => p - 1);
                  window.scrollTo(0, 0);
                }}
                icon={<CaretLeft size={14} weight="bold" />}
              >
                Prev
              </Button>
              <Button
                variant="ghost"
                size="sm"
                disabled={!hasMore}
                onClick={() => {
                  setPage((p) => p + 1);
                  window.scrollTo(0, 0);
                }}
                icon={<CaretRight size={14} weight="bold" />}
              >
                Next
              </Button>
            </div>
          </div>
        </Surface>

        <Surface tone="default" padding="none" radius="xl" className="overflow-hidden">
          {selectedId ? (
            <TargetDetail targetId={selectedId} onClose={() => setSelectedId(null)} />
          ) : (
            <div className="p-5">
              <StateBlock
                tone="muted"
                icon={<Crosshair size={18} weight="bold" />}
                title="No target selected"
                description="Choose a target row to inspect quarantine state, scheduler details, and recent attempts."
              />
            </div>
          )}
        </Surface>
      </div>

      <ImportModal open={showImport} onClose={() => setShowImport(false)} />
    </div>
  );
}
