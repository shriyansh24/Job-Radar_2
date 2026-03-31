import {
  ArrowClockwise,
  CheckCircle,
  Crosshair,
  Plus,
  UploadSimple,
  Warning,
} from "@phosphor-icons/react";
import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { scraperApi, type TargetListParams, type TargetWithAttempts } from "../api/scraper";
import ScraperControlPanel from "../components/scraper/ScraperControlPanel";
import { MetricStrip } from "../components/system/MetricStrip";
import { PageHeader } from "../components/system/PageHeader";
import { StateBlock } from "../components/system/StateBlock";
import { Surface } from "../components/system/Surface";
import { CareerPageModal, type CareerPageDraft } from "../components/targets/CareerPageModal";
import { TargetsFiltersPanel, type TargetsFilters } from "../components/targets/TargetsFiltersPanel";
import { TargetsListPanel } from "../components/targets/TargetsListPanel";
import Button from "../components/ui/Button";
import { toast } from "../components/ui/toastService";
import { TargetDetail } from "../components/targets/TargetDetail";
import { TargetImportModal } from "../components/targets/TargetImportModal";

const pageSize = 50;

function blankCareerPageDraft(): CareerPageDraft {
  return {
    id: null,
    url: "",
    companyName: "",
    enabled: true,
  };
}

export default function Targets() {
  const queryClient = useQueryClient();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [showImport, setShowImport] = useState(false);
  const [careerPageModalOpen, setCareerPageModalOpen] = useState(false);
  const [careerPageDraft, setCareerPageDraft] = useState<CareerPageDraft>(blankCareerPageDraft());
  const [page, setPage] = useState(0);
  const [filters, setFilters] = useState<TargetsFilters>({
    priority_class: "",
    ats_vendor: "",
    status: "",
  });

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
    onError: () => toast("error", "Failed to create career page"),
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
    onError: () => toast("error", "Failed to update career page"),
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
    onError: () => toast("error", "Failed to delete career page"),
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

  return (
    <div className="space-y-6">
      <PageHeader
        className="hero-panel"
        eyebrow="Operations"
        title="Scrape Targets"
        description="Review targets, quarantine state, and batch runs."
        actions={
          <div className="flex flex-wrap gap-2">
            <Button
              variant="secondary"
              size="sm"
              onClick={openCreateCareerPage}
              icon={<Plus size={14} weight="bold" />}
            >
              Add Career Page
            </Button>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setShowImport(true)}
              icon={<UploadSimple size={14} weight="bold" />}
            >
              Import Targets
            </Button>
          </div>
        }
        meta={
          !isLoading ? (
            <div className="font-mono font-bold uppercase tracking-[0.18em]">
              {totalCount} total targets
            </div>
          ) : null
        }
      />

      <MetricStrip
        items={[
          {
            key: "visible",
            label: "Visible targets",
            value: list.length.toLocaleString(),
            hint: "Rows in the current page.",
            icon: <Crosshair size={18} weight="bold" />,
          },
          {
            key: "enabled",
            label: "Enabled",
            value: enabledCount.toLocaleString(),
            hint: "Targets still eligible to run.",
            icon: <CheckCircle size={18} weight="bold" />,
            tone: "success",
          },
          {
            key: "quarantined",
            label: "Quarantined",
            value: quarantinedCount.toLocaleString(),
            hint: "Targets blocked pending review.",
            icon: <Warning size={18} weight="bold" />,
            tone: quarantinedCount ? "warning" : "default",
          },
          {
            key: "vendors",
            label: "ATS vendors",
            value: vendors.size.toLocaleString(),
            hint: "Unique vendors in the result set.",
            icon: <ArrowClockwise size={18} weight="bold" />,
          },
        ]}
      />

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.15fr)_minmax(320px,0.85fr)]">
        <ScraperControlPanel />
        <TargetsFiltersPanel
          filters={filters}
          onPriorityChange={(value) => {
            setFilters((current) => ({ ...current, priority_class: value }));
            setPage(0);
          }}
          onVendorChange={(value) => {
            setFilters((current) => ({ ...current, ats_vendor: value }));
            setPage(0);
          }}
          onStatusChange={(value) => {
            setFilters((current) => ({ ...current, status: value }));
            setPage(0);
          }}
        />
      </div>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.08fr)_minmax(360px,0.92fr)]">
        <TargetsListPanel
          targets={list}
          totalCount={totalCount}
          page={page}
          isLoading={isLoading}
          isError={isError}
          hasMore={hasMore}
          selectedId={selectedId}
          onCreateCareerPage={openCreateCareerPage}
          onSelectTarget={(id) => setSelectedId(id === selectedId ? null : id)}
          onToggleEnabled={(id, enabled) => toggleEnabledMutation.mutate({ id, enabled })}
          onPreviousPage={() => {
            setPage((current) => current - 1);
            window.scrollTo(0, 0);
          }}
          onNextPage={() => {
            setPage((current) => current + 1);
            window.scrollTo(0, 0);
          }}
        />

        <Surface tone="default" padding="none" radius="xl" className="hero-panel overflow-hidden">
          {selectedId ? (
            <TargetDetail
              targetId={selectedId}
              onClose={() => setSelectedId(null)}
              onEditCareerPage={openEditCareerPage}
              onDeleteCareerPage={requestCareerPageDelete}
              deletingCareerPage={deleteCareerPageMutation.isPending}
            />
          ) : (
            <div className="p-5">
              <StateBlock
                tone="muted"
                icon={<Crosshair size={18} weight="bold" />}
                title="No target selected"
                description="Choose a target row to inspect quarantine state, scheduler details, and recent attempts."
              />
            </div>
          )}
        </Surface>
      </div>

      <TargetImportModal open={showImport} onClose={() => setShowImport(false)} />
      <CareerPageModal
        open={careerPageModalOpen}
        draft={careerPageDraft}
        saving={createCareerPageMutation.isPending || updateCareerPageMutation.isPending}
        deleting={deleteCareerPageMutation.isPending}
        onClose={() => {
          setCareerPageModalOpen(false);
          setCareerPageDraft(blankCareerPageDraft());
        }}
        onSave={submitCareerPage}
        onDelete={
          careerPageDraft.id
            ? (draft) => {
                const confirmed = window.confirm(
                  `Delete the career page target for ${draft.companyName || draft.url}?`
                );
                if (confirmed) {
                  deleteCareerPageMutation.mutate(draft.id!);
                }
              }
            : undefined
        }
      />
    </div>
  );
}
