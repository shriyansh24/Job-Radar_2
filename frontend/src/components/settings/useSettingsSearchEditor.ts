import { useCallback, useState } from "react";
import type { SavedSearch } from "../../api/settings";
import type { SearchEditorState } from "./SettingsSearchEditorModal";
import { createBlankSearchEditor } from "./settingsPageState";

function useSettingsSearchEditor() {
  const [searchEditor, setSearchEditor] = useState<SearchEditorState>(createBlankSearchEditor);
  const [searchModalOpen, setSearchModalOpen] = useState(false);

  const openSearchEditor = useCallback((search?: SavedSearch) => {
    if (!search) {
      setSearchEditor(createBlankSearchEditor());
    } else {
      setSearchEditor({
        id: search.id,
        name: search.name,
        filtersText: JSON.stringify(search.filters ?? {}, null, 2),
        alertEnabled: search.alert_enabled,
      });
    }
    setSearchModalOpen(true);
  }, []);

  const closeSearchEditor = useCallback(() => {
    setSearchModalOpen(false);
  }, []);

  const resetSearchEditor = useCallback(() => {
    setSearchEditor(createBlankSearchEditor());
  }, []);

  const updateSearchName = useCallback((value: string) => {
    setSearchEditor((current) => ({
      ...current,
      name: value,
    }));
  }, []);

  const updateSearchFilters = useCallback((value: string) => {
    setSearchEditor((current) => ({
      ...current,
      filtersText: value,
    }));
  }, []);

  const updateSearchAlertEnabled = useCallback((value: boolean) => {
    setSearchEditor((current) => ({
      ...current,
      alertEnabled: value,
    }));
  }, []);

  return {
    searchEditor,
    searchModalOpen,
    openSearchEditor,
    closeSearchEditor,
    resetSearchEditor,
    updateSearchName,
    updateSearchFilters,
    updateSearchAlertEnabled,
  };
}

export { useSettingsSearchEditor };
