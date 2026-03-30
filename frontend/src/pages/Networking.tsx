import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useDeferredValue, useEffect, useState } from "react";
import { jobsApi } from "../api/jobs";
import {
  networkingApi,
  type Contact,
  type ContactCreate,
  type ReferralSuggestion,
} from "../api/networking";
import { NetworkingContactEditorPanel, NetworkingContactPanel } from "../components/networking/NetworkingContactPanel";
import { NetworkingCompanyScanPanel } from "../components/networking/NetworkingCompanyScanPanel";
import { NetworkingReferralDeskPanel } from "../components/networking/NetworkingReferralDeskPanel";
import { NetworkingReferralQueuePanel } from "../components/networking/NetworkingReferralQueuePanel";
import { MetricStrip } from "../components/system/MetricStrip";
import { PageHeader } from "../components/system/PageHeader";
import { Button } from "../components/ui/Button";
import { toast } from "../components/ui/toastService";

const emptyContact: ContactCreate = {
  name: "",
  company: "",
  role: "",
  relationship_strength: 3,
  linkedin_url: "",
  email: "",
  notes: "",
};

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
  const referralQueueItems =
    referralRequests?.map((request) => {
      const requestContact = contacts?.find((contact) => contact.id === request.contact_id);
      return {
        id: request.id,
        contactName: requestContact?.name ?? "Unknown contact",
        jobLabel: `Job ${request.job_id.slice(0, 10)}...`,
        status: request.status,
        messageTemplate: request.message_template,
      };
    }) ?? [];

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
        actions={<Button variant="secondary" onClick={resetForm}>New contact</Button>}
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
        <NetworkingContactPanel
          loadingContacts={loadingContacts}
          filteredContacts={filteredContacts}
          selectedContactId={selectedContactId}
          setSelectedContactId={(id) => {
            setSelectedContactId(id);
            setGeneratedMessage("");
          }}
          setGeneratedMessage={setGeneratedMessage}
          searchValue={searchValue}
          setSearchValue={setSearchValue}
          resetForm={resetForm}
        />

        <div className="space-y-6">
          <NetworkingContactEditorPanel
            selectedContact={selectedContact}
            selectedContactId={selectedContactId}
            form={form}
            setForm={setForm}
            resetForm={resetForm}
            saveContact={saveContact}
            onDelete={() => deleteContactMutation.mutate()}
            deleting={deleteContactMutation.isPending}
          />

          <div className="grid gap-6 xl:grid-cols-2">
            <NetworkingCompanyScanPanel
              companyLookup={companyLookup}
              setCompanyLookup={setCompanyLookup}
              onSearch={() => connectionSearchMutation.mutate(companyLookup)}
              pending={connectionSearchMutation.isPending}
              companyConnections={companyConnections}
            />

            <NetworkingReferralDeskPanel
              selectedJobId={selectedJobId}
              setSelectedJobId={setSelectedJobId}
              jobOptions={jobOptions}
              suggestions={suggestions}
              onSuggest={() => suggestionsMutation.mutate(selectedJobId)}
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
              generatedMessage={generatedMessage}
              setGeneratedMessage={setGeneratedMessage}
              selectedJobLabel={
                selectedJob ? `${selectedJob.title} at ${selectedJob.company_name ?? "Unknown company"}` : null
              }
              pendingSuggestions={suggestionsMutation.isPending}
            />
          </div>

          <NetworkingReferralQueuePanel items={referralQueueItems} />
        </div>
      </div>
    </div>
  );
}
