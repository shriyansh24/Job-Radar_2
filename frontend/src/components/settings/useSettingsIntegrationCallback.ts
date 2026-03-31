import { useEffect } from "react";
import type { QueryClient } from "@tanstack/react-query";
import { toast } from "../ui/toastService";
import type { SettingsTab } from "./SettingsTabNav";

type UseSettingsIntegrationCallbackOptions = {
  queryClient: QueryClient;
  setActiveTab: (tab: SettingsTab) => void;
};

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
      toast("success", `${integrationProvider} connected${integrationMessage ? ` (${integrationMessage})` : ""}`);
      queryClient.invalidateQueries({ queryKey: ["settings", "integrations"] });
    } else {
      toast("error", integrationMessage ?? `${integrationProvider} integration failed`);
    }

    params.delete("integration_status");
    params.delete("integration_provider");
    params.delete("integration_message");
    const nextQuery = params.toString();
    window.history.replaceState({}, document.title, `${window.location.pathname}${nextQuery ? `?${nextQuery}` : ""}`);
  }, [queryClient, setActiveTab]);
}

export { useSettingsIntegrationCallback };
