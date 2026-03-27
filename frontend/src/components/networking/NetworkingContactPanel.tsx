import { MagnifyingGlass, Plus, UserCircle, Buildings, Handshake, LinkSimple, NotePencil, Trash, UsersThree } from "@phosphor-icons/react";
import type { Contact, ContactCreate } from "../../api/networking";
import { Button } from "../ui/Button";
import EmptyState from "../ui/EmptyState";
import Input from "../ui/Input";
import Select from "../ui/Select";
import Skeleton from "../ui/Skeleton";
import Textarea from "../ui/Textarea";
import { ContactRow } from "./ContactRow";

const RELATIONSHIP_OPTIONS = [
  { value: "1", label: "1 - Cold lead" },
  { value: "2", label: "2 - Light familiarity" },
  { value: "3", label: "3 - Warm connection" },
  { value: "4", label: "4 - Strong relationship" },
  { value: "5", label: "5 - Champion" },
];

const PANEL =
  "border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-secondary)]";
const FIELD =
  "!rounded-none !border-2 !border-[var(--color-text-primary)] !bg-[var(--color-bg-secondary)] !text-[var(--color-text-primary)] placeholder:!text-[var(--color-text-muted)] !shadow-none focus:!border-[var(--color-accent-primary)] focus:!ring-0";
const SECONDARY_BUTTON =
  "!rounded-none !border-2 !border-[var(--color-text-primary)] !bg-[var(--color-bg-secondary)] !text-[var(--color-text-primary)] !shadow-none";
const PRIMARY_BUTTON =
  "!rounded-none !border-2 !border-[var(--color-text-primary)] !bg-[var(--color-accent-primary)] !text-white !shadow-none";

export function NetworkingContactPanel({
  loadingContacts,
  filteredContacts,
  selectedContactId,
  setSelectedContactId,
  setGeneratedMessage,
  searchValue,
  setSearchValue,
  resetForm,
}: {
  loadingContacts: boolean;
  filteredContacts: Contact[];
  selectedContactId: string | null;
  setSelectedContactId: (id: string) => void;
  setGeneratedMessage: (value: string) => void;
  searchValue: string;
  setSearchValue: (value: string) => void;
  resetForm: () => void;
}) {
  return (
    <div className={`${PANEL} overflow-hidden`}>
      <div className="border-b-2 border-[var(--color-text-primary)] px-5 py-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <div className="text-sm font-bold uppercase tracking-[0.2em]">Contacts</div>
            <p className="mt-1 text-sm text-[var(--color-text-secondary)]">
              Search and triage the people worth activating.
            </p>
          </div>
          <Button variant="secondary" className={SECONDARY_BUTTON} onClick={resetForm}>
            <Plus size={16} weight="bold" />
            New
          </Button>
        </div>
        <Input
          className={`${FIELD} mt-4`}
          value={searchValue}
          onChange={(event) => setSearchValue(event.target.value)}
          placeholder="Search by name, company, role, or email"
          icon={<MagnifyingGlass size={16} weight="bold" />}
        />
      </div>

      <div className="max-h-[72vh] overflow-auto p-3">
        {loadingContacts ? (
          <div className="space-y-3">
            {Array.from({ length: 6 }).map((_, index) => (
              <Skeleton key={index} variant="rect" className="h-20 w-full" />
            ))}
          </div>
        ) : filteredContacts.length ? (
          <div className="space-y-3">
            {filteredContacts.map((contact) => (
              <ContactRow
                key={contact.id}
                contact={contact}
                selected={selectedContactId === contact.id}
                onClick={() => {
                  setSelectedContactId(contact.id);
                  setGeneratedMessage("");
                }}
              />
            ))}
          </div>
        ) : (
          <EmptyState
            icon={<UsersThree size={32} weight="bold" />}
            title="No contacts yet"
            description="Add referral paths, hiring managers, recruiters, and alumni here."
          />
        )}
      </div>
    </div>
  );
}

export function NetworkingContactEditorPanel({
  selectedContact,
  selectedContactId,
  form,
  setForm,
  resetForm,
  saveContact,
  onDelete,
  deleting,
}: {
  selectedContact: Contact | null;
  selectedContactId: string | null;
  form: ContactCreate;
  setForm: (updater: (current: ContactCreate) => ContactCreate) => void;
  resetForm: () => void;
  saveContact: () => void;
  onDelete: () => void;
  deleting: boolean;
}) {
  return (
    <div className={`${PANEL} p-5 sm:p-6`}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="text-sm font-bold uppercase tracking-[0.2em]">
            {selectedContact ? "Contact detail" : "New contact"}
          </div>
          <p className="mt-1 text-sm leading-6 text-[var(--color-text-secondary)]">
            Keep the record operational: who they are, why they matter, and how to reach them.
          </p>
        </div>
        {selectedContactId ? (
          <Button
            variant="secondary"
            className={SECONDARY_BUTTON}
            onClick={onDelete}
            disabled={deleting}
          >
            <Trash size={16} weight="bold" />
            Delete
          </Button>
        ) : null}
      </div>

      <div className="mt-5 grid gap-4 md:grid-cols-2">
        <Input
          label="Name"
          value={form.name ?? ""}
          onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))}
          placeholder="e.g. Maya Patel"
          icon={<UserCircle size={16} weight="bold" />}
          className={FIELD}
        />
        <Select
          label="Relationship strength"
          value={String(form.relationship_strength ?? 3)}
          onChange={(event) =>
            setForm((current) => ({ ...current, relationship_strength: Number(event.target.value) }))
          }
          options={RELATIONSHIP_OPTIONS}
          className={FIELD}
        />
        <Input
          label="Company"
          value={form.company ?? ""}
          onChange={(event) => setForm((current) => ({ ...current, company: event.target.value }))}
          placeholder="e.g. Stripe"
          icon={<Buildings size={16} weight="bold" />}
          className={FIELD}
        />
        <Input
          label="Role"
          value={form.role ?? ""}
          onChange={(event) => setForm((current) => ({ ...current, role: event.target.value }))}
          placeholder="e.g. Engineering Manager"
          icon={<Handshake size={16} weight="bold" />}
          className={FIELD}
        />
        <Input
          label="Email"
          type="email"
          value={form.email ?? ""}
          onChange={(event) => setForm((current) => ({ ...current, email: event.target.value }))}
          placeholder="maya@company.com"
          className={FIELD}
        />
        <Input
          label="LinkedIn"
          value={form.linkedin_url ?? ""}
          onChange={(event) => setForm((current) => ({ ...current, linkedin_url: event.target.value }))}
          placeholder="https://linkedin.com/in/..."
          icon={<LinkSimple size={16} weight="bold" />}
          className={FIELD}
        />
      </div>

      <Textarea
        label="Notes"
        className={`${FIELD} mt-4 min-h-[140px]`}
        value={form.notes ?? ""}
        onChange={(event) => setForm((current) => ({ ...current, notes: event.target.value }))}
        placeholder="Shared history, timing, team context, or why this person is likely to help."
      />

      <div className="mt-4 flex flex-wrap justify-end gap-3">
        <Button variant="secondary" className={SECONDARY_BUTTON} onClick={resetForm}>
          Reset
        </Button>
        <Button variant="default" className={PRIMARY_BUTTON} onClick={saveContact} disabled={deleting}>
          <NotePencil size={16} weight="bold" />
          {selectedContactId ? "Save changes" : "Create contact"}
        </Button>
      </div>
    </div>
  );
}
