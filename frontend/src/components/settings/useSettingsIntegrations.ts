import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import {
  settingsApi,
  type IntegrationProvider,
  type IntegrationStatus,
} from "../../api/settings";
import { toast } from "../ui/toastService";
import type { SettingsTab } from "./SettingsTabNav";
import { useSettingsIntegrationCallback } from "./useSettingsIntegrationCallback";

type UseSettingsIntegrationsOptions = {
  integrations?: IntegrationStatus[] | null;
  setActiveTab: (tab: SettingsTab) => void;
};

function useSettingsIntegrations({
  integrations,
  setActiveTab,
}: UseSettingsIntegrationsOptions) {
  const queryClient = useQueryClient();
  const [integrationDrafts, setIntegrationDrafts] = useState<Record<string, string>>({});

  useEffect(() => {
    if (!integrations) return;
    setIntegrationDrafts((current) => {
      const next = { ...current };
      for (const integration of integrations) {
        if (!(integration.provider in next)) {
          next[integration.provider] = "";
        }
      }
      return next;
    });
  }, [integrations]);

  useSettingsIntegrationCallback({ queryClient, setActiveTab });

  const integrationUpsertMutation = useMutation({
    mutationFn: async (provider: Exclude<IntegrationProvider, "google">) => {
      const key = integrationDrafts[provider]?.trim();
      if (!key) throw new Error("Enter an API key before saving");
      return settingsApi.upsertIntegration(provider, key);
    },
    onSuccess: (_response, provider) => {
      setIntegrationDrafts((current) => ({ ...current, [provider]: "" }));
      toast("success", `${provider} connected`);
      queryClient.invalidateQueries({ queryKey: ["settings", "integrations"] });
    },
    onError: (error) => {
      const message = error instanceof Error ? error.message : "Failed to save integration";
      toast("error", message);
    },
  });

  const integrationDeleteMutation = useMutation({
    mutationFn: (provider: IntegrationProvider) => settingsApi.deleteIntegration(provider),
    onSuccess: (_response, provider) => {
      toast("success", `${provider} disconnected`);
      queryClient.invalidateQueries({ queryKey: ["settings", "integrations"] });
    },
    onError: () => toast("error", "Failed to disconnect integration"),
  });

  const googleSyncMutation = useMutation({
    mutationFn: () => settingsApi.syncGoogleIntegration(),
    onSuccess: (response) => {
      const result = response.data;
      toast(
        "success",
        `Gmail sync processed ${result.messages_processed}/${result.messages_seen} messages and applied ${result.transitions_applied} updates`
      );
      queryClient.invalidateQueries({ queryKey: ["settings", "integrations"] });
      queryClient.invalidateQueries({ queryKey: ["email", "logs"] });
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
      queryClient.invalidateQueries({ queryKey: ["applications"] });
    },
    onError: (error) => {
      const message = error instanceof Error ? error.message : "Failed to sync Gmail";
      toast("error", message);
    },
  });

  return {
    integrationDrafts,
    savingProvider: integrationUpsertMutation.variables ?? null,
    deletingProvider: integrationDeleteMutation.variables ?? null,
    syncingGoogle: googleSyncMutation.isPending,
    updateIntegrationDraft: (provider: IntegrationProvider, value: string) =>
      setIntegrationDrafts((current) => ({ ...current, [provider]: value })),
    saveIntegration: (provider: Exclude<IntegrationProvider, "google">) =>
      integrationUpsertMutation.mutate(provider),
    deleteIntegration: (provider: IntegrationProvider) =>
      integrationDeleteMutation.mutate(provider),
    connectGoogle: () => {
      window.location.href = settingsApi.buildGoogleConnectUrl("/settings?tab=integrations");
    },
    syncGoogle: () => googleSyncMutation.mutate(),
  };
}

export { useSettingsIntegrations };
