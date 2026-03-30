import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CaretRight, Lightning, LinkSimple, LockOpen, Warning } from "@phosphor-icons/react";
import { scraperApi } from "../../api/scraper";
import { getSafeExternalUrl } from "../../lib/utils";
import Badge from "../ui/Badge";
import Button from "../ui/Button";
import Skeleton from "../ui/Skeleton";
import Toggle from "../ui/Toggle";
import { toast } from "../ui/toastService";
import { AttemptTimeline } from "./AttemptTimeline";
import { priorityVariant, atsVariant, relativeTime } from "./targetUtils";

export function TargetDetail({
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
    <div className="flex h-full flex-col">
      <div className="hero-panel flex shrink-0 items-center justify-between px-5 py-4">
        <div>
          <div className="font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-text-muted">
            Target Detail
          </div>
          <div className="mt-2 max-w-xs truncate text-xl font-black uppercase tracking-[-0.05em] text-text-primary">
            {isLoading ? (
              <Skeleton variant="text" className="h-4 w-32" />
            ) : (
              target?.company_name ?? target?.url ?? "-"
            )}
          </div>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="hard-press border-2 border-border bg-card p-2 text-text-muted hover:text-text-primary"
          aria-label="Close detail panel"
        >
          <CaretRight size={16} weight="bold" />
        </button>
      </div>

      {isLoading ? (
        <div className="space-y-4 p-5">
          <Skeleton variant="text" className="h-5 w-3/4" />
          <Skeleton variant="text" className="h-4 w-1/2" />
          <Skeleton variant="rect" className="h-28 w-full" />
          <Skeleton variant="rect" className="h-28 w-full" />
        </div>
      ) : !target ? null : (
        <div className="flex-1 space-y-5 overflow-auto p-5">
          <div className="flex flex-wrap gap-2">
            <Badge variant={priorityVariant(target.priority_class)}>{target.priority_class}</Badge>
            <Badge variant={atsVariant(target.ats_vendor)}>{target.ats_vendor ?? "unknown"}</Badge>
            {target.quarantined ? <Badge variant="danger">quarantined</Badge> : null}
            {!target.enabled ? <Badge variant="default">disabled</Badge> : null}
          </div>

          <div className="space-y-1">
            <p className="text-xs font-medium uppercase tracking-wide text-text-muted">URL</p>
            {safeTargetUrl ? (
              <a
                href={safeTargetUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-start gap-1 break-all text-sm text-accent-primary hover:underline"
              >
                <LinkSimple size={14} className="mt-0.5 shrink-0" />
                {safeTargetUrl}
              </a>
            ) : (
              <span className="break-all text-sm text-text-secondary">{target.url}</span>
            )}
          </div>

          <div className="grid grid-cols-2 gap-3">
            {[
              { label: "Source Kind", value: target.source_kind },
              { label: "ATS Board Token", value: target.ats_board_token ?? "-" },
              { label: "Schedule Interval", value: `${target.schedule_interval_m}m` },
              { label: "Tiers", value: `${target.start_tier} to ${target.max_tier}` },
              { label: "Last Success", value: relativeTime(target.last_success_at) },
              { label: "Last Failure", value: relativeTime(target.last_failure_at) },
              { label: "Consecutive Failures", value: String(target.consecutive_failures) },
              { label: "Total Failures", value: String(target.failure_count) },
              {
                label: "Last HTTP Status",
                value: target.last_http_status != null ? String(target.last_http_status) : "-",
              },
              { label: "Next Scheduled", value: relativeTime(target.next_scheduled_at) },
            ].map(({ label, value }) => (
              <div key={label} className="brutal-panel px-4 py-3">
                <p className="font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-text-muted">
                  {label}
                </p>
                <p className="mt-3 truncate text-sm text-text-primary">{value}</p>
              </div>
            ))}
          </div>

          {target.quarantined && target.quarantine_reason ? (
            <div className="flex items-start gap-3 border-2 border-[var(--color-accent-danger)] bg-[var(--color-accent-danger-subtle)] px-4 py-4">
              <Warning size={16} weight="fill" className="mt-0.5 shrink-0 text-accent-danger" />
              <div>
                <p className="font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-accent-danger">
                  Quarantine Reason
                </p>
                <p className="mt-2 text-sm text-text-secondary">{target.quarantine_reason}</p>
              </div>
            </div>
          ) : null}

          <div className="space-y-2">
            <p className="text-xs font-medium uppercase tracking-wide text-text-muted">Actions</p>
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
              {target.quarantined ? (
                <Button
                  variant="secondary"
                  size="sm"
                  loading={releaseMutation.isPending}
                  onClick={() => releaseMutation.mutate(target.id)}
                  icon={<LockOpen size={14} weight="bold" />}
                >
                  Release
                </Button>
              ) : null}
            </div>
            <div className="flex items-center gap-3 pt-1">
              <Toggle
                checked={target.enabled}
                onChange={(checked) => toggleMutation.mutate({ id: target.id, enabled: checked })}
                disabled={toggleMutation.isPending}
              />
              <span className="text-sm text-text-secondary">{target.enabled ? "Enabled" : "Disabled"}</span>
            </div>
          </div>

          <div className="space-y-2">
            <p className="text-xs font-medium uppercase tracking-wide text-text-muted">Recent Attempts</p>
            <AttemptTimeline attempts={target.recent_attempts ?? []} />
          </div>

          <div className="space-y-0.5 border-t border-border/50 pt-2 text-xs text-text-muted">
            <p>Created {relativeTime(target.created_at)}</p>
            <p>Updated {relativeTime(target.updated_at)}</p>
          </div>
        </div>
      )}
    </div>
  );
}
