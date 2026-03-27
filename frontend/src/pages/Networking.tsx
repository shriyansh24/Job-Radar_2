import {
  Buildings,
  ChatsCircle,
  Handshake,
  LinkSimple,
  MagnifyingGlass,
  NotePencil,
  PaperPlaneTilt,
  Plus,
  Trash,
  UserCircle,
  UsersThree,
} from "@phosphor-icons/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { formatDistanceToNow } from "date-fns";
import { useDeferredValue, useEffect, useState } from "react";
import { jobsApi } from "../api/jobs";
import {
  networkingApi,
  type Contact,
  type ContactCreate,
  type ReferralSuggestion,
} from "../api/networking";
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

const RELATIONSHIP_OPTIONS = [
  { value: "1", label: "1 - Cold lead" },
  { value: "2", label: "2 - Light familiarity" },
  { value: "3", label: "3 - Warm connection" },
  { value: "4", label: "4 - Strong relationship" },
  { value: "5", label: "5 - Champion" },
];

const emptyContact: ContactCreate = {
  name: "",
  company: "",
  role: "",
  relationship_strength: 3,
  linkedin_url: "",
  email: "",
  notes: "",
};

const PANEL =
  "border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-secondary)] shadow-[4px_4px_0px_0px_var(--color-text-primary)]";
const PANEL_ALT =
  "border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-primary)] shadow-[4px_4px_0px_0px_var(--color-text-primary)]";
const FIELD =
  "!rounded-none !border-2 !border-[var(--color-text-primary)] !bg-[var(--color-bg-secondary)] !text-[var(--color-text-primary)] placeholder:!text-[var(--color-text-muted)] !shadow-none focus:!border-[var(--color-accent-primary)] focus:!ring-0";
const SECONDARY_BUTTON =
  "!rounded-none !border-2 !border-[var(--color-text-primary)] !bg-[var(--color-bg-secondary)] !text-[var(--color-text-primary)] !shadow-[4px_4px_0px_0px_var(--color-text-primary)]";
const PRIMARY_BUTTON =
  "!rounded-none !border-2 !border-[var(--color-text-primary)] !bg-[var(--color-accent-primary)] !text-white !shadow-[4px_4px_0px_0px_var(--color-text-primary)]";

function ContactRow({
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
          ? "border-[var(--color-text-primary)] bg-[var(--color-accent-primary-subtle)] shadow-[4px_4px_0px_0px_var(--color-accent-primary)]"
          : "border-[var(--color-text-primary)] bg-[var(--color-bg-secondary)] shadow-[4px_4px_0px_0px_var(--color-text-primary)] hover:-translate-x-[2px] hover:-translate-y-[2px]"
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

function SuggestionCard({
  suggestion,
  selectedJobId,
  onDraft,
  onCreate,
}: {
  suggestion: ReferralSuggestion;
  selectedJobId: string;
  onDraft: (contactId: string) => void;
  onCreate: (contactId: string, message?: string | null) => void;
}) {
  return (
    <div className={`${PANEL_ALT} p-4`}>
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-sm font-bold uppercase tracking-[0.08em]">{suggestion.contact.name}</div>
          <div className="mt-1 text-sm text-[var(--color-text-secondary)]">
            {[suggestion.contact.role, suggestion.contact.company].filter(Boolean).join(" - ")}
          </div>
        </div>
        <Badge variant="success" className="rounded-none">
          Suggested
        </Badge>
      </div>
      <p className="mt-3 text-sm leading-6 text-[var(--color-text-secondary)]">{suggestion.relevance_reason}</p>
      {suggestion.suggested_message ? (
        <div className="mt-3 border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-primary)] px-3 py-3 text-sm leading-6">
          {suggestion.suggested_message}
        </div>
      ) : null}
      <div className="mt-4 flex flex-wrap gap-2">
        <Button
          variant="secondary"
          className={SECONDARY_BUTTON}
          onClick={() => onDraft(suggestion.contact.id)}
        >
          <ChatsCircle size={16} weight="bold" />
          Draft outreach
        </Button>
        <Button
          variant="default"
          className={PRIMARY_BUTTON}
          onClick={() => onCreate(suggestion.contact.id, suggestion.suggested_message ?? null)}
        >
          <PaperPlaneTilt size={16} weight="bold" />
          Create request
        </Button>
      </div>
      <div className="mt-3 text-[10px] font-bold uppercase tracking-[0.2em] text-[var(--color-text-muted)]">
        Target job {selectedJobId.slice(0, 12)}
      </div>
    </div>
  );
}

export default function Networking() {
  const queryClient = useQueryClient();
  const [selectedContactId, setSelectedContactId] = useState<string | null>(null);
  const [form, setForm] = useState<ContactCreate>({ ...emptyContact });
  const [searchValue, setSearchValue] = useState("");
  const [companyLookup, setCompanyLookup] = useState("");
  const [selectedJobId, setSelectedJobId] = useState("");
  const [generatedMessage, setGeneratedMessage] = useState("");
  const [suggestions, setSuggestions] = useState<ReferralSuggestion[]>([]);
  const [companyConnections, setCompanyConnections] = useState<Contact[]>([]);
  const deferredSearch = useDeferredValue(searchValue);

  const { data: contacts, isLoading: loadingContacts } = useQuery({
    queryKey: ["networking", "contacts"],
    queryFn: () => networkingApi.listContacts().then((response) => response.data),
  });

  const { data: referralRequests } = useQuery({
    queryKey: ["networking", "referral-requests"],
    queryFn: () => networkingApi.listReferralRequests().then((response) => response.data),
  });

  const { data: recentJobs } = useQuery({
    queryKey: ["jobs", "networking-context"],
    queryFn: () =>
      jobsApi
        .list({ page_size: 12, sort_by: "scraped_at", sort_order: "desc" })
        .then((response) => response.data),
  });

  useEffect(() => {
    if (!selectedJobId && recentJobs?.items.length) {
      setSelectedJobId(recentJobs.items[0].id);
    }
  }, [recentJobs, selectedJobId]);

  useEffect(() => {
    if (!contacts?.length) return;
    if (!selectedContactId) return;

    const selected = contacts.find((contact) => contact.id === selectedContactId);
    if (selected) {
      setForm({
        name: selected.name,
        company: selected.company ?? "",
        role: selected.role ?? "",
        relationship_strength: selected.relationship_strength,
        linkedin_url: selected.linkedin_url ?? "",
        email: selected.email ?? "",
        notes: selected.notes ?? "",
      });
    }
  }, [contacts, selectedContactId]);

  const filteredContacts =
    contacts?.filter((contact) => {
      const query = deferredSearch.trim().toLowerCase();
      if (!query) return true;
      return [contact.name, contact.company, contact.role, contact.email]
        .filter(Boolean)
        .some((value) => value?.toLowerCase().includes(query));
    }) ?? [];

  const selectedContact = contacts?.find((contact) => contact.id === selectedContactId) ?? null;

  const createContactMutation = useMutation({
    mutationFn: (payload: ContactCreate) => networkingApi.createContact(payload).then((response) => response.data),
    onSuccess: (contact) => {
      toast("success", "Contact added");
      queryClient.invalidateQueries({ queryKey: ["networking", "contacts"] });
      setSelectedContactId(contact.id);
    },
    onError: () => toast("error", "Failed to add contact"),
  });

  const updateContactMutation = useMutation({
    mutationFn: (payload: ContactCreate) =>
      networkingApi.updateContact(selectedContactId!, payload).then((response) => response.data),
    onSuccess: () => {
      toast("success", "Contact updated");
      queryClient.invalidateQueries({ queryKey: ["networking", "contacts"] });
    },
    onError: () => toast("error", "Failed to update contact"),
  });

  const deleteContactMutation = useMutation({
    mutationFn: () => networkingApi.deleteContact(selectedContactId!),
    onSuccess: () => {
      toast("success", "Contact deleted");
      queryClient.invalidateQueries({ queryKey: ["networking", "contacts"] });
      setSelectedContactId(null);
      setForm({ ...emptyContact });
    },
    onError: () => toast("error", "Failed to delete contact"),
  });

  const connectionSearchMutation = useMutation({
    mutationFn: (company: string) => networkingApi.findConnections(company).then((response) => response.data),
    onSuccess: (results) => {
      setCompanyConnections(results);
    },
    onError: () => toast("error", "Failed to look up connections"),
  });

  const suggestionsMutation = useMutation({
    mutationFn: (jobId: string) => networkingApi.suggestReferrals(jobId).then((response) => response.data),
    onSuccess: (results) => {
      setSuggestions(results);
      if (!results.length) {
        toast("info", "No referral suggestions for that job yet");
      }
    },
    onError: () => toast("error", "Failed to fetch referral suggestions"),
  });

  const outreachMutation = useMutation({
    mutationFn: (payload: { contactId: string; jobId: string }) =>
      networkingApi.generateOutreach(payload.contactId, payload.jobId).then((response) => response.data),
    onSuccess: (response) => {
      setGeneratedMessage(response.message);
    },
    onError: () => toast("error", "Failed to draft outreach"),
  });

  const createReferralRequestMutation = useMutation({
    mutationFn: (payload: { contactId: string; jobId: string; message: string }) =>
      networkingApi
        .createReferralRequest({
          contact_id: payload.contactId,
          job_id: payload.jobId,
          message_template: payload.message || undefined,
        })
        .then((response) => response.data),
    onSuccess: () => {
      toast("success", "Referral request draft created");
      queryClient.invalidateQueries({ queryKey: ["networking", "referral-requests"] });
    },
    onError: () => toast("error", "Failed to create referral request"),
  });

  const saveContact = () => {
    if (!form.name?.trim()) {
      toast("error", "Name is required");
      return;
    }

    const payload: ContactCreate = {
      name: form.name.trim(),
      company: form.company?.trim() || null,
      role: form.role?.trim() || null,
      relationship_strength: Number(form.relationship_strength ?? 3),
      linkedin_url: form.linkedin_url?.trim() || null,
      email: form.email?.trim() || null,
      notes: form.notes?.trim() || null,
    };

    if (selectedContactId) {
      updateContactMutation.mutate(payload);
    } else {
      createContactMutation.mutate(payload);
    }
  };

  const resetForm = () => {
    setSelectedContactId(null);
    setForm({ ...emptyContact });
    setGeneratedMessage("");
  };

  const strengthAverage =
    contacts && contacts.length
      ? (contacts.reduce((sum, contact) => sum + contact.relationship_strength, 0) / contacts.length).toFixed(1)
      : "0.0";

  const jobOptions =
    recentJobs?.items.map((job) => ({
      value: job.id,
        label: `${job.title} - ${job.company_name ?? "Unknown company"}`,
    })) ?? [];

  const selectedJob = recentJobs?.items.find((job) => job.id === selectedJobId) ?? null;

  const heroMetrics = [
    {
      label: "Contacts",
      value: String(contacts?.length ?? 0),
      accent: "text-[var(--color-accent-primary)]",
      description: "People you can actually route through.",
    },
    {
      label: "Avg strength",
      value: strengthAverage,
      accent: "text-[var(--color-accent-success)]",
      description: "Relationship confidence across the network.",
    },
    {
      label: "Referral queue",
      value: String(referralRequests?.length ?? 0),
      accent: "text-[var(--color-accent-warning)]",
      description: "Drafted asks waiting for follow-through.",
    },
  ];

  return (
    <div className="space-y-6 px-4 py-4 sm:px-6 lg:px-8">
      <PageHeader
        eyebrow="Execute"
        title="Networking"
        description="A referral CRM with harsh borders, fast scanning, and a direct path from contact to outreach draft."
        meta={
          <>
            <span className="border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-tertiary)] px-3 py-2 font-mono text-[10px] font-bold uppercase tracking-[0.16em]">
              {contacts?.length ?? 0} contacts
            </span>
            <span className="border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-tertiary)] px-3 py-2 font-mono text-[10px] font-bold uppercase tracking-[0.16em]">
              {referralRequests?.length ?? 0} referral drafts
            </span>
            <span className="border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-tertiary)] px-3 py-2 font-mono text-[10px] font-bold uppercase tracking-[0.16em]">
              {selectedJobId ? "Targeted" : "Idle"}
            </span>
          </>
        }
        actions={
          <Button variant="secondary" className={SECONDARY_BUTTON} onClick={resetForm}>
            <Plus size={16} weight="bold" />
            New contact
          </Button>
        }
      />

      <MetricStrip
        items={heroMetrics.map((metric) => ({
          key: metric.label,
          label: metric.label,
          value: metric.value,
          hint: metric.description,
          tone:
            metric.accent === "text-[var(--color-accent-success)]"
              ? "success"
              : metric.accent === "text-[var(--color-accent-warning)]"
                ? "warning"
                : "default",
        }))}
      />

      <div className="grid gap-6 xl:grid-cols-[minmax(320px,0.95fr)_minmax(0,1.05fr)]">
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

        <div className="space-y-6">
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
                  onClick={() => deleteContactMutation.mutate()}
                  disabled={deleteContactMutation.isPending}
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
              <Button
                variant="default"
                className={PRIMARY_BUTTON}
                onClick={saveContact}
                disabled={createContactMutation.isPending || updateContactMutation.isPending}
              >
                <NotePencil size={16} weight="bold" />
                {selectedContactId ? "Save changes" : "Create contact"}
              </Button>
            </div>
          </div>

          <div className="grid gap-6 xl:grid-cols-2">
            <div className={`${PANEL} p-5 sm:p-6`}>
              <div className="text-sm font-bold uppercase tracking-[0.2em]">Company connection scan</div>
              <p className="mt-2 text-sm leading-6 text-[var(--color-text-secondary)]">
                Find the warmest existing relationships before you ask for a referral.
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
                  onClick={() => connectionSearchMutation.mutate(companyLookup)}
                  disabled={!companyLookup.trim() || connectionSearchMutation.isPending}
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
                    title="No connection results yet"
                    description="Run a company scan to see which contacts map to that target."
                  />
                )}
              </div>
            </div>

            <div className={`${PANEL} p-5 sm:p-6`}>
              <div className="text-sm font-bold uppercase tracking-[0.2em]">Referral desk</div>
              <p className="mt-2 text-sm leading-6 text-[var(--color-text-secondary)]">
                Pull suggestions for a job, draft outreach, and create a referral request in one pass.
              </p>
              <div className="mt-4 space-y-4">
                <Select
                  label="Target job"
                  value={selectedJobId}
                  onChange={(event) => setSelectedJobId(event.target.value)}
                  options={jobOptions}
                  placeholder="Choose a job"
                  className={FIELD}
                />
                <Button
                  variant="secondary"
                  className={SECONDARY_BUTTON}
                  onClick={() => suggestionsMutation.mutate(selectedJobId)}
                  disabled={!selectedJobId || suggestionsMutation.isPending}
                >
                  <Handshake size={16} weight="bold" />
                  Suggest referrals
                </Button>
              </div>

              <div className="mt-4 space-y-3">
                {suggestions.length ? (
                  suggestions.map((suggestion) => (
                    <SuggestionCard
                      key={suggestion.contact.id}
                      suggestion={suggestion}
                      selectedJobId={selectedJobId}
                      onDraft={(contactId) =>
                        outreachMutation.mutate({
                          contactId,
                          jobId: selectedJobId,
                        })
                      }
                      onCreate={(contactId, message) =>
                        createReferralRequestMutation.mutate({
                          contactId,
                          jobId: selectedJobId,
                          message: generatedMessage || message || "",
                        })
                      }
                    />
                  ))
                ) : (
                  <EmptyState
                    icon={<Handshake size={28} weight="bold" />}
                    title="No referral suggestions loaded"
                    description="Choose a job and ask the system for the best available warm paths."
                  />
                )}
              </div>

              {generatedMessage ? (
                <Textarea
                  label="Generated outreach"
                  className={`${FIELD} mt-4 min-h-[160px]`}
                  value={generatedMessage}
                  onChange={(event) => setGeneratedMessage(event.target.value)}
                />
              ) : null}
              {selectedJob ? (
                <p className="mt-3 text-xs font-bold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">
                  Current target: {selectedJob.title} at {selectedJob.company_name ?? "Unknown company"}
                </p>
              ) : null}
            </div>
          </div>

          <div className={`${PANEL} p-5 sm:p-6`}>
            <div className="flex items-center gap-2 text-sm font-bold uppercase tracking-[0.18em]">
              <PaperPlaneTilt size={16} weight="bold" className="text-[var(--color-accent-primary)]" />
              Referral request queue
            </div>
            <div className="mt-4 space-y-3">
              {referralRequests?.length ? (
                referralRequests.map((request) => {
                  const requestContact = contacts?.find((contact) => contact.id === request.contact_id);
                  return (
                    <div key={request.id} className={`${PANEL_ALT} px-4 py-4`}>
                      <div className="flex flex-wrap items-center justify-between gap-3">
                        <div>
                          <div className="text-sm font-bold uppercase tracking-[0.08em]">
                            {requestContact?.name ?? "Unknown contact"}
                          </div>
                          <div className="mt-1 text-sm text-[var(--color-text-secondary)]">
                            Job {request.job_id.slice(0, 10)}... - {request.status}
                          </div>
                        </div>
                        <Badge variant={request.status === "draft" ? "warning" : "info"} className="rounded-none">
                          {request.status}
                        </Badge>
                      </div>
                      {request.message_template ? (
                        <p className="mt-3 line-clamp-3 text-sm leading-6 text-[var(--color-text-secondary)]">
                          {request.message_template}
                        </p>
                      ) : null}
                    </div>
                  );
                })
              ) : (
                <EmptyState
                  icon={<PaperPlaneTilt size={28} weight="bold" />}
                  title="No referral requests yet"
                  description="Create drafts from the referral desk so asks do not disappear into notes."
                />
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
