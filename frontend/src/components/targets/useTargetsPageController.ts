import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { AxiosError } from "axios";
import { scraperApi, type TargetListParams, type TargetWithAttempts } from "../../api/scraper";
import type { CareerPageDraft } from "./CareerPageModal";
import type { TargetsFilters } from "./TargetsFiltersPanel";
import { toast } from "../ui/toastService";

const pageSize = 50;

function getApiErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof AxiosError) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string" && detail.trim()) {
      return detail;
    }
  }
  if (error instanceof Error && error.message.trim()) {
    return error.message;
  }
  return fallback;
}

function blankCareerPageDraft(): CareerPageDraft {
  return {
    id: null,
    url: "",
    companyName: "",
    enabled: true,
  };
}

function createInitialFilters(): TargetsFilters {
  return {
    priority_class: "",
    ats_vendor: "",
    status: "",
  };
}

function useTargetsPageController() {
  const queryClient = useQueryClient();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [showImport, setShowImport] = useState(false);
  const [careerPageModalOpen, setCareerPageModalOpen] = useState(false);
  const [careerPageDraft, setCareerPageDraft] = useState<CareerPageDraft>(blankCareerPageDraft());
  const [page, setPage] = useState(0);
  const [filters, setFilters] = useState<TargetsFilters>(createInitialFilters());

  const apiParams: TargetListParams = {
    limit: pageSize,
    offset: page * pageSize,
  };
  if (filters.priority_class) apiParams.priority_class = filters.priority_class;
  if (filters.ats_vendor) apiParams.ats_vendor = filters.ats_vendor;
  if (filters.status === "enabled") apiParams.enabled = true;
  if (filters.status === "disabled") apiParams.enabled = false;
  if (filters.status === "quarantined") apiParams.quarantined = true;

  const { data: targets, isLoading, isError } = useQuery({
    queryKey: ["targets", apiParams],
    queryFn: () => scraperApi.listTargets(apiParams).then((r) => r.data),
    placeholderData: keepPreviousData,
  });

  const toggleEnabledMutation = useMutation({
    mutationFn: ({ id, enabled }: { id: string; enabled: boolean }) =>
      scraperApi.updateTarget(id, { enabled }),
    onSuccess: (_, vars) => {
      toast("success", vars.enabled ? "Target enabled" : "Target disabled");
      queryClient.invalidateQueries({ queryKey: ["targets"] });
      if (selectedId) queryClient.invalidateQueries({ queryKey: ["target", selectedId] });
    },
    onError: () => toast("error", "Failed to update target"),
  });

  const createCareerPageMutation = useMutation({
    mutationFn: (draft: CareerPageDraft) =>
      scraperApi.createCareerPage({
        url: draft.url,
        company_name: draft.companyName || undefined,
      }),
    onSuccess: () => {
      toast("success", "Career page created");
      queryClient.invalidateQueries({ queryKey: ["targets"] });
      setCareerPageModalOpen(false);
      setCareerPageDraft(blankCareerPageDraft());
    },
    onError: (error) => toast("error", getApiErrorMessage(error, "Failed to create career page")),
  });

  const updateCareerPageMutation = useMutation({
    mutationFn: (draft: CareerPageDraft) =>
      scraperApi.updateCareerPage(draft.id!, {
        url: draft.url,
        company_name: draft.companyName || undefined,
        enabled: draft.enabled,
      }),
    onSuccess: (_response, draft) => {
      toast("success", "Career page updated");
      queryClient.invalidateQueries({ queryKey: ["targets"] });
      if (draft.id) {
        queryClient.invalidateQueries({ queryKey: ["target", draft.id] });
      }
      setCareerPageModalOpen(false);
      setCareerPageDraft(blankCareerPageDraft());
    },
    onError: (error) => toast("error", getApiErrorMessage(error, "Failed to update career page")),
  });

  const deleteCareerPageMutation = useMutation({
    mutationFn: (id: string) => scraperApi.deleteCareerPage(id),
    onSuccess: (_response, id) => {
      toast("success", "Career page deleted");
      queryClient.invalidateQueries({ queryKey: ["targets"] });
      queryClient.removeQueries({ queryKey: ["target", id] });
      if (selectedId === id) {
        setSelectedId(null);
      }
      setCareerPageModalOpen(false);
      setCareerPageDraft(blankCareerPageDraft());
    },
    onError: (error) => toast("error", getApiErrorMessage(error, "Failed to delete career page")),
  });

  const list = targets?.items ?? [];
  const totalCount = targets?.total ?? 0;
  const hasMore = list.length === pageSize;
  const enabledCount = list.filter((target) => target.enabled).length;
  const quarantinedCount = list.filter((target) => target.quarantined).length;
  const vendors = new Set(list.map((target) => target.ats_vendor || "unknown"));

  function openCreateCareerPage() {
    setCareerPageDraft(blankCareerPageDraft());
    setCareerPageModalOpen(true);
  }

  function openEditCareerPage(target: TargetWithAttempts) {
    setCareerPageDraft({
      id: target.id,
      url: target.url,
      companyName: target.company_name ?? "",
      enabled: target.enabled,
    });
    setCareerPageModalOpen(true);
  }

  function submitCareerPage(draft: CareerPageDraft) {
    if (draft.id) {
      updateCareerPageMutation.mutate(draft);
      return;
    }
    createCareerPageMutation.mutate(draft);
  }

  function requestCareerPageDelete(target: TargetWithAttempts) {
    const confirmed = window.confirm(
      `Delete the career page target for ${target.company_name ?? target.url}?`
    );
    if (!confirmed) {
      return;
    }
    deleteCareerPageMutation.mutate(target.id);
  }

  function setPriorityClass(value: string) {
    setFilters((current) => ({ ...current, priority_class: value }));
    setPage(0);
  }

  function setVendor(value: string) {
    setFilters((current) => ({ ...current, ats_vendor: value }));
    setPage(0);
  }

  function setStatus(value: string) {
    setFilters((current) => ({ ...current, status: value }));
    setPage(0);
  }

  return {
    selectedId,
    setSelectedId,
    showImport,
    setShowImport,
    careerPageModalOpen,
    careerPageDraft,
    page,
    setPage,
    filters,
    list,
    totalCount,
    hasMore,
    enabledCount,
    quarantinedCount,
    vendors,
    isLoading,
    isError,
    toggleEnabled: (id: string, enabled: boolean) =>
      toggleEnabledMutation.mutate({ id, enabled }),
    openCreateCareerPage,
    openEditCareerPage,
    submitCareerPage,
    requestCareerPageDelete,
    deleteCareerPageById: (id: string) => deleteCareerPageMutation.mutate(id),
    setPriorityClass,
    setVendor,
    setStatus,
    closeCareerPageModal: () => {
      setCareerPageModalOpen(false);
      setCareerPageDraft(blankCareerPageDraft());
    },
    careerPageDeleting: deleteCareerPageMutation.isPending,
    careerPageSaving:
      createCareerPageMutation.isPending || updateCareerPageMutation.isPending,
  };
}

export { useTargetsPageController };
