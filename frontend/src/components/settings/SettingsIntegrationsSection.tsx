import { Key, Trash } from "@phosphor-icons/react";
import Badge from "../ui/Badge";
import Button from "../ui/Button";
import Input from "../ui/Input";
import Skeleton from "../ui/Skeleton";
import { SettingsSection } from "../system/SettingsSection";
import type { IntegrationStatus } from "../../api/settings";
import { INTEGRATION_LABELS, INTEGRATION_NOTES } from "./constants";

type SettingsIntegrationsSectionProps = {
  userEmail?: string | null;
  integrations?: IntegrationStatus[] | null;
  drafts: Record<string, string>;
  loading: boolean;
  onDraftChange: (provider: IntegrationStatus["provider"], value: string) => void;
  onSave: (provider: IntegrationStatus["provider"]) => void;
  onDelete: (provider: IntegrationStatus["provider"]) => void;
  savingProvider?: IntegrationStatus["provider"] | null;
  deletingProvider?: IntegrationStatus["provider"] | null;
};

function SettingsIntegrationsSection({
  userEmail,
  integrations,
  drafts,
  loading,
  onDraftChange,
  onSave,
  onDelete,
  savingProvider,
  deletingProvider,
}: SettingsIntegrationsSectionProps) {
  return (
    <SettingsSection title="Integrations" description="Manage stored provider keys." className="border-2 border-border bg-card shadow-hard-xl">
      <div className="space-y-4 p-6">
        {loading ? (
          Array.from({ length: 4 }).map((_, index) => <Skeleton key={index} variant="rect" className="h-28 w-full" />)
        ) : (
          integrations?.map((integration) => {
            const draft = drafts[integration.provider] ?? "";
            return (
              <div key={integration.provider} className="border-2 border-border p-4">
                <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                  <div className="space-y-2">
                    <div className="flex flex-wrap items-center gap-2">
                      <h4 className="text-sm font-bold uppercase tracking-[0.12em] text-foreground">
                        {INTEGRATION_LABELS[integration.provider]}
                      </h4>
                      <Badge variant={integration.connected ? "success" : "default"} size="sm" className="rounded-none">
                        {integration.status.replace("_", " ")}
                      </Badge>
                    </div>
                    <p className="max-w-2xl text-sm text-muted-foreground">{INTEGRATION_NOTES[integration.provider]}</p>
                    <p className="text-xs text-muted-foreground">
                      {integration.masked_value ?? "No key saved"} |{" "}
                      {integration.updated_at
                        ? new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(new Date(integration.updated_at))
                        : "Never checked"}
                    </p>
                  </div>

                  <form
                    className="w-full max-w-xl space-y-3"
                    onSubmit={(event) => {
                      event.preventDefault();
                      onSave(integration.provider);
                    }}
                  >
                    <input
                      type="text"
                      name={`${integration.provider}-username`}
                      autoComplete="username"
                      value={userEmail ?? ""}
                      readOnly
                      tabIndex={-1}
                      aria-hidden="true"
                      className="sr-only"
                    />
                    <Input
                      label="API key"
                      type="password"
                      autoComplete="off"
                      name={`${integration.provider}-api-key`}
                      value={draft}
                      onChange={(event) => onDraftChange(integration.provider, event.target.value)}
                      placeholder={`Enter ${INTEGRATION_LABELS[integration.provider]} key`}
                    />
                    <div className="flex flex-wrap justify-end gap-2">
                      <Button
                        type="button"
                        variant="secondary"
                        onClick={() => onDelete(integration.provider)}
                        loading={deletingProvider === integration.provider}
                        icon={<Trash size={16} weight="bold" />}
                      >
                        Disconnect
                      </Button>
                      <Button type="submit" loading={savingProvider === integration.provider} icon={<Key size={16} weight="bold" />}>
                        Save key
                      </Button>
                    </div>
                  </form>
                </div>
              </div>
            );
          })
        )}
      </div>
    </SettingsSection>
  );
}

export { SettingsIntegrationsSection };
export type { SettingsIntegrationsSectionProps };
