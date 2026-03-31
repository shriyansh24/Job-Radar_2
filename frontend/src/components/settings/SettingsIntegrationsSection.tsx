import { ArrowsClockwise, Key, LinkSimple, Trash } from "@phosphor-icons/react";
import Badge from "../ui/Badge";
import Button from "../ui/Button";
import Input from "../ui/Input";
import Skeleton from "../ui/Skeleton";
import { SettingsSection } from "../system/SettingsSection";
import type { IntegrationProvider, IntegrationStatus } from "../../api/settings";
import { INTEGRATION_LABELS, INTEGRATION_NOTES } from "./constants";

type SettingsIntegrationsSectionProps = {
  userEmail?: string | null;
  integrations?: IntegrationStatus[] | null;
  drafts: Record<string, string>;
  loading: boolean;
  onDraftChange: (provider: IntegrationProvider, value: string) => void;
  onSave: (provider: Exclude<IntegrationProvider, "google">) => void;
  onDelete: (provider: IntegrationProvider) => void;
  onConnectGoogle: () => void;
  onSyncGoogle: () => void;
  savingProvider?: IntegrationProvider | null;
  deletingProvider?: IntegrationProvider | null;
  syncingGoogle?: boolean;
};

function SettingsIntegrationsSection({
  userEmail,
  integrations,
  drafts,
  loading,
  onDraftChange,
  onSave,
  onDelete,
  onConnectGoogle,
  onSyncGoogle,
  savingProvider,
  deletingProvider,
  syncingGoogle,
}: SettingsIntegrationsSectionProps) {
  return (
    <SettingsSection title="Integrations" description="Manage provider credentials and Gmail sync." className="border-2 border-border bg-card shadow-hard-xl">
      <div className="space-y-4 p-6">
        {loading ? (
          Array.from({ length: 5 }).map((_, index) => <Skeleton key={index} variant="rect" className="h-28 w-full" />)
        ) : (
          integrations?.map((integration) => {
            const draft = drafts[integration.provider] ?? "";
            const googleIntegration = integration.provider === "google";
            const showGoogleDisconnect = googleIntegration && integration.status !== "not_configured";
            const showGoogleSync = googleIntegration && integration.status === "connected";
            const updatedLabel = integration.updated_at
              ? new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(new Date(integration.updated_at))
              : "Never checked";
            const lastSyncedLabel = integration.last_synced_at
              ? new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(new Date(integration.last_synced_at))
              : "Never synced";

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
                      {googleIntegration ? (
                        <>
                          {integration.account_email ?? "No account connected"} | Last sync {lastSyncedLabel}
                        </>
                      ) : (
                        <>
                          {integration.masked_value ?? "No key saved"} | {updatedLabel}
                        </>
                      )}
                    </p>
                    {integration.scopes.length > 0 ? (
                      <p className="text-xs text-muted-foreground">Scopes: {integration.scopes.join(", ")}</p>
                    ) : null}
                    {integration.last_error ? (
                      <p className="text-xs text-red-600 dark:text-red-300">{integration.last_error}</p>
                    ) : null}
                  </div>

                  {googleIntegration ? (
                    <div className="w-full max-w-xl space-y-3">
                      <div className="flex flex-wrap justify-end gap-2">
                        {showGoogleDisconnect ? (
                          <Button
                            type="button"
                            variant="secondary"
                            onClick={() => onDelete(integration.provider)}
                            loading={deletingProvider === integration.provider}
                            icon={<Trash size={16} weight="bold" />}
                          >
                            Disconnect
                          </Button>
                        ) : null}
                        {showGoogleSync ? (
                          <Button
                            type="button"
                            variant="secondary"
                            onClick={onSyncGoogle}
                            loading={Boolean(syncingGoogle)}
                            icon={<ArrowsClockwise size={16} weight="bold" />}
                          >
                            Sync Gmail
                          </Button>
                        ) : null}
                        <Button
                          type="button"
                          onClick={onConnectGoogle}
                          icon={<LinkSimple size={16} weight="bold" />}
                        >
                          {integration.status === "not_configured" ? "Connect Google" : "Reconnect Google"}
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <form
                      className="w-full max-w-xl space-y-3"
                      onSubmit={(event) => {
                        event.preventDefault();
                        onSave(integration.provider as Exclude<IntegrationProvider, "google">);
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
                  )}
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
