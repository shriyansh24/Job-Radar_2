import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { adminApi } from "../../api/admin";
import { deleteAccountApi } from "../../api/auth";
import { toast } from "../ui/toastService";

function useSettingsDataActions() {
  const queryClient = useQueryClient();
  const [clearConfirm, setClearConfirm] = useState("");
  const [deleteConfirm, setDeleteConfirm] = useState("");

  const deleteAccountMutation = useMutation({
    mutationFn: () => deleteAccountApi(),
    onSuccess: () => toast("success", "Account deletion requested"),
    onError: () => toast("error", "Account deletion failed"),
  });

  const clearDataMutation = useMutation({
    mutationFn: () => adminApi.clearData(),
    onSuccess: (response) => {
      toast("success", `Cleared ${response.data.rows_deleted} rows`);
      queryClient.invalidateQueries();
    },
    onError: () => toast("error", "Failed to clear data"),
  });

  async function handleExport() {
    try {
      const response = await adminApi.exportData();
      const blob = response.data;
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `jobradar-export-${new Date().toISOString().slice(0, 10)}.json`;
      anchor.click();
      URL.revokeObjectURL(url);
      toast("success", "Export started");
    } catch {
      toast("error", "Failed to export data");
    }
  }

  return {
    clearConfirm,
    deleteConfirm,
    clearReady: clearConfirm.trim().toLowerCase() === "clear",
    deleteReady: deleteConfirm.trim().toLowerCase() === "delete",
    clearPending: clearDataMutation.isPending,
    deletePending: deleteAccountMutation.isPending,
    setClearConfirm,
    setDeleteConfirm,
    exportData: handleExport,
    clearData: () => clearDataMutation.mutate(),
    deleteAccount: () => deleteAccountMutation.mutate(),
  };
}

export { useSettingsDataActions };
