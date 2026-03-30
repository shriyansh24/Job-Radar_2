import {
  ArrowClockwise,
  CaretLeft,
  CaretRight,
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
import Button from "../components/ui/Button";
import EmptyState from "../components/ui/EmptyState";
import Select from "../components/ui/Select";
import { toast } from "../components/ui/toastService";
import { TargetDetail } from "../components/targets/TargetDetail";
import { TargetImportModal } from "../components/targets/TargetImportModal";
import { TargetRow } from "../components/targets/TargetRow";
import { TargetRowSkeleton } from "../components/targets/TargetRowSkeleton";

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
  const [filters, setFilters] = useState<{
    priority_class: string;
    ats_vendor: string;
    status: string;
  }>({
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

        <Surface tone="default" padding="lg" radius="xl" className="hero-panel">
          <div className="grid gap-4 md:grid-cols-3 xl:grid-cols-1">
            <Select
              value={filters.priority_class}
              onChange={(event) => {
                setFilters((current) => ({ ...current, priority_class: event.target.value }));
                setPage(0);
              }}
              options={[
                { value: "watchlist", label: "Watchlist" },
                { value: "hot", label: "Hot" },
                { value: "warm", label: "Warm" },
                { value: "cool", label: "Cool" },
              ]}
              placeholder="All priorities"
              label="Priority"
            />
            <Select
              value={filters.ats_vendor}
              onChange={(event) => {
                setFilters((current) => ({ ...current, ats_vendor: event.target.value }));
                setPage(0);
              }}
              options={[
                { value: "greenhouse", label: "Greenhouse" },
                { value: "lever", label: "Lever" },
                { value: "ashby", label: "Ashby" },
                { value: "workday", label: "Workday" },
                { value: "unknown", label: "Unknown" },
              ]}
              placeholder="All vendors"
              label="ATS vendor"
            />
            <Select
              value={filters.status}
              onChange={(event) => {
                setFilters((current) => ({ ...current, status: event.target.value }));
                setPage(0);
              }}
              options={[
                { value: "enabled", label: "Enabled" },
                { value: "disabled", label: "Disabled" },
                { value: "quarantined", label: "Quarantined" },
              ]}
              placeholder="All statuses"
              label="Status"
            />
          </div>
        </Surface>
      </div>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.08fr)_minmax(360px,0.92fr)]">
        <Surface tone="default" padding="none" radius="xl" className="brutal-panel overflow-hidden">
          <div className="border-b-2 border-border px-5 py-4">
            <div className="flex items-baseline justify-between gap-3">
              <div>
                <div className="text-sm font-black uppercase tracking-[-0.03em] text-text-primary">
                  Targets
                </div>
                <div className="mt-1 text-sm text-muted-foreground">
                  <span className="font-mono text-text-secondary">{list.length}</span> of {totalCount} shown
                </div>
              </div>
              <div className="font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
                Page {page + 1}
              </div>
            </div>
          </div>

          <div className="min-h-[420px]">
            {isError ? (
              <div className="p-8 text-center text-sm text-accent-danger">
                Failed to load targets. Please try again.
              </div>
            ) : isLoading ? (
              Array.from({ length: 10 }).map((_, index) => <TargetRowSkeleton key={index} />)
            ) : list.length === 0 ? (
              <div className="p-6">
                <EmptyState
                  icon={<Crosshair size={40} weight="bold" />}
                  title="No targets found"
                  description="Import targets or adjust your filters"
                  action={{ label: "Add Career Page", onClick: openCreateCareerPage }}
                />
              </div>
            ) : (
              list.map((target) => (
                <TargetRow
                  key={target.id}
                  target={target}
                  isSelected={target.id === selectedId}
                  onClick={() => setSelectedId(target.id === selectedId ? null : target.id)}
                  onToggleEnabled={(enabled) =>
                    toggleEnabledMutation.mutate({ id: target.id, enabled })
                  }
                />
              ))
            )}
          </div>

          <div className="flex items-center justify-between border-t-2 border-border px-5 py-3">
            <span className="text-xs text-text-muted">
              Page <span className="font-mono text-text-secondary">{page + 1}</span>
            </span>
            <div className="flex gap-1">
              <Button
                variant="ghost"
                size="sm"
                disabled={page === 0}
                onClick={() => {
                  setPage((current) => current - 1);
                  window.scrollTo(0, 0);
                }}
                icon={<CaretLeft size={14} weight="bold" />}
              >
                Prev
              </Button>
              <Button
                variant="ghost"
                size="sm"
                disabled={!hasMore}
                onClick={() => {
                  setPage((current) => current + 1);
                  window.scrollTo(0, 0);
                }}
                icon={<CaretRight size={14} weight="bold" />}
              >
                Next
              </Button>
            </div>
          </div>
        </Surface>

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
