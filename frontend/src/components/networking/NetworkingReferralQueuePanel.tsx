import { PaperPlaneTilt } from "@phosphor-icons/react";
import Badge from "../ui/Badge";
import EmptyState from "../ui/EmptyState";

const PANEL =
  "border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-secondary)]";
const PANEL_ALT =
  "border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-primary)]";

export function NetworkingReferralQueuePanel({
  items,
}: {
  items: Array<{
    id: string;
    contactName: string;
    jobLabel: string;
    status: string;
    messageTemplate?: string | null;
  }>;
}) {
  return (
    <div className={`${PANEL} p-5 sm:p-6`}>
      <div className="flex items-center gap-2 text-sm font-bold uppercase tracking-[0.18em]">
        <PaperPlaneTilt size={16} weight="bold" className="text-[var(--color-accent-primary)]" />
        Referral request queue
      </div>
      <div className="mt-4 space-y-3">
        {items.length ? (
          items.map((request) => (
            <div key={request.id} className={`${PANEL_ALT} px-4 py-4`}>
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <div className="text-sm font-bold uppercase tracking-[0.08em]">{request.contactName}</div>
                  <div className="mt-1 text-sm text-[var(--color-text-secondary)]">
                    {request.jobLabel} - {request.status}
                  </div>
                </div>
                <Badge variant={request.status === "draft" ? "warning" : "info"} className="rounded-none">
                  {request.status}
                </Badge>
              </div>
              {request.messageTemplate ? (
                <p className="mt-3 line-clamp-3 text-sm leading-6 text-[var(--color-text-secondary)]">
                  {request.messageTemplate}
                </p>
              ) : null}
            </div>
          ))
        ) : (
          <EmptyState
            icon={<PaperPlaneTilt size={28} weight="bold" />}
            title="No referral requests yet"
            description="Create drafts from the referral desk so asks do not disappear into notes."
          />
        )}
      </div>
    </div>
  );
}
