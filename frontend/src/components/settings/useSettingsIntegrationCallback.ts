import { useEffect } from "react";
import type { QueryClient } from "@tanstack/react-query";
import { toast } from "../ui/toastService";
import type { SettingsTab } from "./SettingsTabNav";

type UseSettingsIntegrationCallbackOptions = {
  queryClient: QueryClient;
  setActiveTab: (tab: SettingsTab) => void;
};

const CALLBACK_MESSAGE_TEXT: Record<string, string> = {
  google_connected: "Google Gmail connected.",
  google_oauth_denied: "Google connection was cancelled before access was granted.",
  google_oauth_callback_failed: "Google connection failed before the account could be linked.",
  missing_oauth_callback_params: "Google sign-in did not return the required callback parameters.",
};

function formatCallbackMessage(
  integrationStatus: string,
  integrationProvider: string,
  integrationMessage: string | null,
) {
  if (integrationMessage && CALLBACK_MESSAGE_TEXT[integrationMessage]) {
    return CALLBACK_MESSAGE_TEXT[integrationMessage];
  }
  if (integrationStatus === "connected") {
    return `${integrationProvider} connected`;
  }
  return integrationMessage ?? `${integrationProvider} integration failed`;
}

function useSettingsIntegrationCallback({
  queryClient,
  setActiveTab,
}: UseSettingsIntegrationCallbackOptions) {
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get("tab") === "integrations") {
      setActiveTab("integrations");
    }

    const integrationStatus = params.get("integration_status");
    const integrationProvider = params.get("integration_provider");
    const integrationMessage = params.get("integration_message");
    if (!integrationStatus || !integrationProvider) {
      return;
    }

    if (integrationStatus === "connected") {
      toast(
        "success",
        formatCallbackMessage(integrationStatus, integrationProvider, integrationMessage)
      );
      queryClient.invalidateQueries({ queryKey: ["settings", "integrations"] });
    } else {
      toast(
        "error",
        formatCallbackMessage(integrationStatus, integrationProvider, integrationMessage)
      );
    }

    params.delete("integration_status");
    params.delete("integration_provider");
    params.delete("integration_message");
    const nextQuery = params.toString();
    window.history.replaceState({}, document.title, `${window.location.pathname}${nextQuery ? `?${nextQuery}` : ""}`);
  }, [queryClient, setActiveTab]);
}

export { useSettingsIntegrationCallback };
