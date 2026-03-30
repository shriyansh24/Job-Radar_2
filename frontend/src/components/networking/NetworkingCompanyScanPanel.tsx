import { Buildings, MagnifyingGlass } from "@phosphor-icons/react";
import type { Contact } from "../../api/networking";
import Badge from "../ui/Badge";
import { Button } from "../ui/Button";
import EmptyState from "../ui/EmptyState";
import Input from "../ui/Input";

const PANEL =
  "border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-secondary)]";
const PANEL_ALT =
  "border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-primary)]";
const FIELD =
  "!rounded-none !border-2 !border-[var(--color-text-primary)] !bg-[var(--color-bg-secondary)] !text-[var(--color-text-primary)] placeholder:!text-[var(--color-text-muted)] !shadow-none focus:!border-[var(--color-accent-primary)] focus:!ring-0";
const SECONDARY_BUTTON =
  "!rounded-none !border-2 !border-[var(--color-text-primary)] !bg-[var(--color-bg-secondary)] !text-[var(--color-text-primary)] !shadow-none";

export function NetworkingCompanyScanPanel({
  companyLookup,
  setCompanyLookup,
  onSearch,
  pending,
  companyConnections,
}: {
  companyLookup: string;
  setCompanyLookup: (value: string) => void;
  onSearch: () => void;
  pending: boolean;
  companyConnections: Contact[];
}) {
  return (
    <div className={`${PANEL} p-5 sm:p-6`}>
      <div className="text-sm font-bold uppercase tracking-[0.2em]">Company scan</div>
      <p className="mt-2 text-sm leading-6 text-[var(--color-text-secondary)]">
        Search a company and see which contacts can open a door.
      </p>
      <div className="mt-4 flex flex-col gap-3 sm:flex-row">
        <Input
          value={companyLookup}
          onChange={(event) => setCompanyLookup(event.target.value)}
          placeholder="Search a company"
          icon={<Buildings size={16} weight="bold" />}
          className={FIELD}
        />
        <Button
          variant="secondary"
          className={SECONDARY_BUTTON}
          onClick={onSearch}
          disabled={!companyLookup.trim() || pending}
        >
          <MagnifyingGlass size={16} weight="bold" />
          Find
        </Button>
      </div>

      <div className="mt-4 space-y-3">
        {companyConnections.length ? (
          companyConnections.map((contact) => (
            <div key={contact.id} className={`${PANEL_ALT} px-4 py-3`}>
              <div className="flex items-center justify-between gap-3">
                <div>
                  <div className="text-sm font-bold uppercase tracking-[0.08em]">{contact.name}</div>
                  <div className="text-sm text-[var(--color-text-secondary)]">
                    {[contact.role, contact.company].filter(Boolean).join(" - ")}
                  </div>
                </div>
                <Badge variant={contact.relationship_strength >= 4 ? "success" : "info"} className="rounded-none">
                  {contact.relationship_strength}/5
                </Badge>
              </div>
            </div>
          ))
        ) : (
          <EmptyState
            icon={<Buildings size={28} weight="bold" />}
            title="No connection results"
            description="Run a scan to see which contacts map to the company."
          />
        )}
      </div>
    </div>
  );
}
