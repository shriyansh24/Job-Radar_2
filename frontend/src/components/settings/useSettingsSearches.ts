import { useMutation, useQueryClient } from "@tanstack/react-query";
import { settingsApi, type SavedSearch } from "../../api/settings";
import { toast } from "../ui/toastService";
import { useSettingsSearchEditor } from "./useSettingsSearchEditor";
import { parseSearchFilters } from "./settingsPageState";

function useSettingsSearches() {
  const queryClient = useQueryClient();
  const {
    searchEditor,
    searchModalOpen,
    openSearchEditor,
    closeSearchEditor,
    resetSearchEditor,
    updateSearchName,
    updateSearchFilters,
    updateSearchAlertEnabled,
  } = useSettingsSearchEditor();

  const saveSearchMutation = useMutation({
    mutationFn: async () => {
      const filters = parseSearchFilters(searchEditor.filtersText);
      const payload = {
        name: searchEditor.name.trim(),
        filters,
        alert_enabled: searchEditor.alertEnabled,
      };

      if (searchEditor.id) {
        return settingsApi.updateSearch(searchEditor.id, payload);
      }

      return settingsApi.createSearch(payload);
    },
    onSuccess: () => {
      toast("success", searchEditor.id ? "Search updated" : "Search created");
      resetSearchEditor();
      closeSearchEditor();
      queryClient.invalidateQueries({ queryKey: ["settings", "searches"] });
    },
    onError: (error) => {
      const message = error instanceof Error ? error.message : "Failed to save search";
      toast("error", message);
    },
  });

  const deleteSearchMutation = useMutation({
    mutationFn: (id: string) => settingsApi.deleteSearch(id),
    onSuccess: () => {
      toast("success", "Search deleted");
      queryClient.invalidateQueries({ queryKey: ["settings", "searches"] });
    },
    onError: () => toast("error", "Failed to delete search"),
  });

  const checkSearchMutation = useMutation({
    mutationFn: (id: string) => settingsApi.checkSearch(id),
    onSuccess: (response) => {
      const result = response.data;
      toast(
        "success",
        result.new_matches
          ? `${result.new_matches} new job${result.new_matches === 1 ? "" : "s"} found`
          : "No new jobs matched this search"
      );
      queryClient.invalidateQueries({ queryKey: ["settings", "searches"] });
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
    },
    onError: () => toast("error", "Failed to check saved search"),
  });

  function toggleSearch(search: SavedSearch) {
    settingsApi
      .updateSearch(search.id, { alert_enabled: !search.alert_enabled })
      .then(() => {
        toast("success", "Search updated");
        queryClient.invalidateQueries({ queryKey: ["settings", "searches"] });
      })
      .catch(() => toast("error", "Failed to update search"));
  }

  return {
    searchEditor,
    searchModalOpen,
    checkingSearchId: checkSearchMutation.variables ?? null,
    isSavingSearch: saveSearchMutation.isPending,
    openSearchEditor,
    closeSearchEditor,
    updateSearchName,
    updateSearchFilters,
    updateSearchAlertEnabled,
    saveSearch: () => saveSearchMutation.mutate(),
    checkSearch: (search: SavedSearch) => checkSearchMutation.mutate(search.id),
    deleteSearch: (search: SavedSearch) => deleteSearchMutation.mutate(search.id),
    toggleSearch,
  };
}

export { useSettingsSearches };
