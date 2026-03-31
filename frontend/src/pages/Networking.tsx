import { NetworkingContactEditorPanel, NetworkingContactPanel } from "../components/networking/NetworkingContactPanel";
import { NetworkingCompanyScanPanel } from "../components/networking/NetworkingCompanyScanPanel";
import { NetworkingReferralDeskPanel } from "../components/networking/NetworkingReferralDeskPanel";
import { NetworkingReferralQueuePanel } from "../components/networking/NetworkingReferralQueuePanel";
import { MetricStrip } from "../components/system/MetricStrip";
import { PageHeader } from "../components/system/PageHeader";
import { Button } from "../components/ui/Button";
import { useNetworkingContacts } from "../hooks/useNetworkingContacts";
import { useNetworkingReferrals } from "../hooks/useNetworkingReferrals";

export default function Networking() {
  const {
    contacts,
    companyConnections,
    companyLookup,
    connectionSearchMutation,
    deleteContactMutation,
    filteredContacts,
    form,
    loadingContacts,
    resetForm: resetContactForm,
    saveContact,
    searchValue,
    selectedContact,
    selectedContactId,
    setCompanyLookup,
    setForm,
    setSearchValue,
    setSelectedContactId,
  } = useNetworkingContacts();
  const {
    createReferralRequestMutation,
    generatedMessage,
    jobOptions,
    outreachMutation,
    referralQueueItems,
    referralRequests,
    selectedJob,
    selectedJobId,
    setGeneratedMessage,
    setSelectedJobId,
    suggestions,
    suggestionsMutation,
  } = useNetworkingReferrals({ contacts });

  const resetForm = () => {
    resetContactForm();
    setGeneratedMessage("");
  };

  const heroMetrics = [
    {
      label: "Contacts",
      value: String(contacts.length),
      accent: "text-[var(--color-accent-primary)]",
      description: "People you can actually route through.",
    },
    {
      label: "Avg strength",
      value:
        contacts.length
          ? (contacts.reduce((sum, contact) => sum + contact.relationship_strength, 0) / contacts.length).toFixed(1)
          : "0.0",
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
              {contacts.length} contacts
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
