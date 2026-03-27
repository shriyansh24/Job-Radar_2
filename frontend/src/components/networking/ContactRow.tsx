import { formatDistanceToNow } from "date-fns";
import type { Contact } from "../../api/networking";
import Badge from "../ui/Badge";
import { cn } from "../../lib/utils";

export function ContactRow({
  contact,
  selected,
  onClick,
}: {
  contact: Contact;
  selected: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
    className={cn(
        "w-full border-2 px-4 py-4 text-left transition-transform duration-150",
        selected
          ? "border-[var(--color-text-primary)] bg-[var(--color-accent-primary-subtle)]"
          : "border-[var(--color-text-primary)] bg-[var(--color-bg-secondary)] hover:-translate-x-[2px] hover:-translate-y-[2px]"
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="truncate text-sm font-bold uppercase tracking-[0.08em] text-[var(--color-text-primary)]">
            {contact.name}
          </div>
          <div className="mt-1 truncate text-sm text-[var(--color-text-secondary)]">
            {[contact.role, contact.company].filter(Boolean).join(" - ") || "No role or company yet"}
          </div>
        </div>
        <Badge variant={contact.relationship_strength >= 4 ? "success" : "info"} className="rounded-none">
          {contact.relationship_strength}/5
        </Badge>
      </div>
      <div className="mt-3 flex flex-wrap items-center gap-3 text-xs text-[var(--color-text-muted)]">
        {contact.email ? <span>{contact.email}</span> : null}
        {contact.last_contacted ? (
          <span>Last touch {formatDistanceToNow(new Date(contact.last_contacted), { addSuffix: true })}</span>
        ) : null}
      </div>
    </button>
  );
}
