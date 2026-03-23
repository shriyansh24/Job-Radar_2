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

const RELATIONSHIP_OPTIONS = [
  { value: "1", label: "1 • Cold lead" },
  { value: "2", label: "2 • Light familiarity" },
  { value: "3", label: "3 • Warm connection" },
  { value: "4", label: "4 • Strong relationship" },
  { value: "5", label: "5 • Champion" },
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

function MetricCard({
  label,
  value,
  description,
}: {
  label: string;
  value: string;
  description: string;
}) {
  return (
    <Card className="p-5">
      <div className="text-[11px] font-medium uppercase tracking-[0.18em] text-text-muted">{label}</div>
      <div className="mt-2 text-2xl font-semibold tracking-tight text-text-primary">{value}</div>
      <p className="mt-2 text-sm text-text-secondary">{description}</p>
    </Card>
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
      label: `${job.title} • ${job.company_name ?? "Unknown company"}`,
    })) ?? [];

  const selectedJob = recentJobs?.items.find((job) => job.id === selectedJobId) ?? null;

  return (
    <div className="space-y-6">
      <Card className="overflow-hidden p-0">
        <div className="grid gap-5 border-b border-border bg-[linear-gradient(135deg,color-mix(in_srgb,var(--accent-primary)_10%,transparent),transparent_62%)] px-6 py-6 lg:grid-cols-[minmax(0,1.8fr)_minmax(0,1fr)]">
          <div>
            <div className="text-xs font-medium uppercase tracking-[0.18em] text-text-muted">Execute</div>
            <h1 className="mt-2 text-3xl font-semibold tracking-tight text-text-primary">Networking</h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-text-secondary">
              A lightweight referral CRM shaped by Wix-style contact management and a Clay-like
              outreach assistant. Capture warm paths, draft asks, and keep requests visible.
            </p>
          </div>
          <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-1">
            <MetricCard
              label="Contacts"
              value={String(contacts?.length ?? 0)}
              description="People you can actually route through."
            />
            <MetricCard
              label="Avg Strength"
              value={strengthAverage}
              description="Relationship confidence across the network."
            />
            <MetricCard
              label="Referral Queue"
              value={String(referralRequests?.length ?? 0)}
              description="Drafted asks waiting for follow-through."
            />
          </div>
        </div>
      </Card>

      <div className="grid gap-6 xl:grid-cols-[minmax(320px,0.9fr)_minmax(0,1.3fr)]">
        <Card className="p-0">
          <div className="border-b border-border px-5 py-4">
            <div className="flex items-center justify-between gap-3">
              <div>
                <div className="text-sm font-semibold text-text-primary">Contacts</div>
                <p className="mt-1 text-sm text-text-secondary">Search and triage the people worth activating.</p>
              </div>
              <Button variant="secondary" onClick={resetForm}>
                <Plus size={16} weight="bold" />
                New
              </Button>
            </div>
            <Input
              className="mt-4"
              value={searchValue}
              onChange={(event) => setSearchValue(event.target.value)}
              placeholder="Search by name, company, role, or email"
              icon={<MagnifyingGlass size={16} weight="bold" />}
            />
          </div>

          <div className="max-h-[720px] overflow-auto px-3 py-3">
            {loadingContacts ? (
              <div className="space-y-3 px-2 py-2">
                {Array.from({ length: 6 }).map((_, index) => (
                  <Skeleton key={index} variant="rect" className="h-20 w-full" />
                ))}
              </div>
            ) : filteredContacts.length ? (
              filteredContacts.map((contact) => (
                <button
                  key={contact.id}
                  type="button"
                  onClick={() => {
                    setSelectedContactId(contact.id);
                    setGeneratedMessage("");
                  }}
                  className={cn(
                    "mb-2 w-full rounded-[var(--radius-xl)] border px-4 py-4 text-left transition-colors",
                    selectedContactId === contact.id
                      ? "border-accent-primary/35 bg-accent-primary/8"
                      : "border-transparent bg-bg-secondary hover:border-border hover:bg-bg-tertiary"
                  )}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="truncate text-sm font-medium text-text-primary">{contact.name}</div>
                      <div className="mt-1 truncate text-sm text-text-secondary">
                        {[contact.role, contact.company].filter(Boolean).join(" • ") || "No role or company yet"}
                      </div>
                    </div>
                    <Badge variant={contact.relationship_strength >= 4 ? "success" : "info"}>
                      {contact.relationship_strength}/5
                    </Badge>
                  </div>
                  <div className="mt-3 flex items-center gap-3 text-xs text-text-muted">
                    {contact.email ? <span>{contact.email}</span> : null}
                    {contact.last_contacted ? (
                      <span>Last touch {formatDistanceToNow(new Date(contact.last_contacted), { addSuffix: true })}</span>
                    ) : null}
                  </div>
                </button>
              ))
            ) : (
              <EmptyState
                icon={<UsersThree size={32} weight="bold" />}
                title="No contacts yet"
                description="Add referral paths, hiring managers, recruiters, and alumni here."
              />
            )}
          </div>
        </Card>

        <div className="space-y-6">
          <Card className="p-5">
            <div className="flex items-center justify-between gap-3">
              <div>
                <div className="text-sm font-semibold text-text-primary">
                  {selectedContact ? "Contact detail" : "New contact"}
                </div>
                <p className="mt-1 text-sm text-text-secondary">
                  Keep the record operational: who they are, why they matter, and how to reach them.
                </p>
              </div>
              {selectedContactId ? (
                <Button
                  variant="destructive"
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
              />
              <Select
                label="Relationship strength"
                value={String(form.relationship_strength ?? 3)}
                onChange={(event) =>
                  setForm((current) => ({ ...current, relationship_strength: Number(event.target.value) }))
                }
                options={RELATIONSHIP_OPTIONS}
              />
              <Input
                label="Company"
                value={form.company ?? ""}
                onChange={(event) => setForm((current) => ({ ...current, company: event.target.value }))}
                placeholder="e.g. Stripe"
                icon={<Buildings size={16} weight="bold" />}
              />
              <Input
                label="Role"
                value={form.role ?? ""}
                onChange={(event) => setForm((current) => ({ ...current, role: event.target.value }))}
                placeholder="e.g. Engineering Manager"
                icon={<Handshake size={16} weight="bold" />}
              />
              <Input
                label="Email"
                type="email"
                value={form.email ?? ""}
                onChange={(event) => setForm((current) => ({ ...current, email: event.target.value }))}
                placeholder="maya@company.com"
              />
              <Input
                label="LinkedIn"
                value={form.linkedin_url ?? ""}
                onChange={(event) => setForm((current) => ({ ...current, linkedin_url: event.target.value }))}
                placeholder="https://linkedin.com/in/..."
                icon={<LinkSimple size={16} weight="bold" />}
              />
            </div>

            <Textarea
              label="Notes"
              className="mt-4 min-h-[140px]"
              value={form.notes ?? ""}
              onChange={(event) => setForm((current) => ({ ...current, notes: event.target.value }))}
              placeholder="Shared history, timing, team context, or why this person is likely to help."
            />

            <div className="mt-4 flex flex-wrap justify-end gap-3">
              <Button variant="secondary" onClick={resetForm}>
                Reset
              </Button>
              <Button
                variant="default"
                onClick={saveContact}
                disabled={createContactMutation.isPending || updateContactMutation.isPending}
              >
                <NotePencil size={16} weight="bold" />
                {selectedContactId ? "Save changes" : "Create contact"}
              </Button>
            </div>
          </Card>

          <div className="grid gap-6 xl:grid-cols-2">
            <Card className="p-5">
              <div className="text-sm font-semibold text-text-primary">Company connection scan</div>
              <p className="mt-1 text-sm text-text-secondary">
                Find the warmest existing relationships before you ask for a referral.
              </p>
              <div className="mt-4 flex gap-3">
                <Input
                  value={companyLookup}
                  onChange={(event) => setCompanyLookup(event.target.value)}
                  placeholder="Search a company"
                  icon={<Buildings size={16} weight="bold" />}
                />
                <Button
                  variant="secondary"
                  onClick={() => connectionSearchMutation.mutate(companyLookup)}
                  disabled={!companyLookup.trim() || connectionSearchMutation.isPending}
                >
                  <MagnifyingGlass size={16} weight="bold" />
                  Find
                </Button>
              </div>

              <div className="mt-4 space-y-2">
                {companyConnections.length ? (
                  companyConnections.map((contact) => (
                    <div
                      key={contact.id}
                      className="rounded-[var(--radius-lg)] border border-border bg-bg-secondary px-4 py-3"
                    >
                      <div className="flex items-center justify-between gap-3">
                        <div>
                          <div className="text-sm font-medium text-text-primary">{contact.name}</div>
                          <div className="text-sm text-text-secondary">
                            {[contact.role, contact.company].filter(Boolean).join(" • ")}
                          </div>
                        </div>
                        <Badge variant={contact.relationship_strength >= 4 ? "success" : "info"}>
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
            </Card>

            <Card className="p-5">
              <div className="text-sm font-semibold text-text-primary">Referral desk</div>
              <p className="mt-1 text-sm text-text-secondary">
                Pull suggestions for a job, draft outreach, and create a referral request in one pass.
              </p>
              <div className="mt-4 space-y-4">
                <Select
                  label="Target job"
                  value={selectedJobId}
                  onChange={(event) => setSelectedJobId(event.target.value)}
                  options={jobOptions}
                  placeholder="Choose a job"
                />
                <Button
                  variant="secondary"
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
                    <div
                      key={suggestion.contact.id}
                      className="rounded-[var(--radius-lg)] border border-border bg-bg-secondary px-4 py-4"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <div className="text-sm font-medium text-text-primary">{suggestion.contact.name}</div>
                          <div className="text-sm text-text-secondary">
                            {[suggestion.contact.role, suggestion.contact.company].filter(Boolean).join(" • ")}
                          </div>
                        </div>
                        <Badge variant="success">Suggested</Badge>
                      </div>
                      <p className="mt-3 text-sm leading-6 text-text-secondary">{suggestion.relevance_reason}</p>
                      {suggestion.suggested_message ? (
                        <div className="mt-3 rounded-[var(--radius-lg)] border border-border bg-bg-primary px-3 py-3 text-sm leading-6 text-text-secondary">
                          {suggestion.suggested_message}
                        </div>
                      ) : null}
                      <div className="mt-4 flex flex-wrap gap-2">
                        <Button
                          variant="secondary"
                          onClick={() =>
                            outreachMutation.mutate({
                              contactId: suggestion.contact.id,
                              jobId: selectedJobId,
                            })
                          }
                        >
                          <ChatsCircle size={16} weight="bold" />
                          Draft outreach
                        </Button>
                        <Button
                          variant="default"
                          onClick={() =>
                            createReferralRequestMutation.mutate({
                              contactId: suggestion.contact.id,
                              jobId: selectedJobId,
                              message: generatedMessage || suggestion.suggested_message,
                            })
                          }
                        >
                          <PaperPlaneTilt size={16} weight="bold" />
                          Create request
                        </Button>
                      </div>
                    </div>
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
                  className="mt-4 min-h-[160px]"
                  value={generatedMessage}
                  onChange={(event) => setGeneratedMessage(event.target.value)}
                />
              ) : null}
              {selectedJob ? (
                <p className="mt-3 text-xs text-text-muted">
                  Current target: {selectedJob.title} at {selectedJob.company_name ?? "Unknown company"}
                </p>
              ) : null}
            </Card>
          </div>

          <Card className="p-5">
            <div className="flex items-center gap-2 text-sm font-semibold text-text-primary">
              <PaperPlaneTilt size={16} weight="bold" className="text-accent-primary" />
              Referral request queue
            </div>
            <div className="mt-4 space-y-3">
              {referralRequests?.length ? (
                referralRequests.map((request) => {
                  const requestContact = contacts?.find((contact) => contact.id === request.contact_id);
                  return (
                    <div
                      key={request.id}
                      className="rounded-[var(--radius-lg)] border border-border bg-bg-secondary px-4 py-4"
                    >
                      <div className="flex flex-wrap items-center justify-between gap-3">
                        <div>
                          <div className="text-sm font-medium text-text-primary">
                            {requestContact?.name ?? "Unknown contact"}
                          </div>
                          <div className="mt-1 text-sm text-text-secondary">
                            Job {request.job_id.slice(0, 10)}... • {request.status}
                          </div>
                        </div>
                        <Badge variant={request.status === "draft" ? "warning" : "info"}>{request.status}</Badge>
                      </div>
                      {request.message_template ? (
                        <p className="mt-3 line-clamp-3 text-sm leading-6 text-text-secondary">
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
          </Card>
        </div>
      </div>
    </div>
  );
}
