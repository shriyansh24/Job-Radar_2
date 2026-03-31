import {
  ArrowClockwise,
  CheckCircle,
  Crosshair,
  Plus,
  UploadSimple,
  Warning,
} from "@phosphor-icons/react";
import { PageHeader } from "../components/system/PageHeader";
import { MetricStrip } from "../components/system/MetricStrip";
import { StateBlock } from "../components/system/StateBlock";
import { Surface } from "../components/system/Surface";
import ScraperControlPanel from "../components/scraper/ScraperControlPanel";
import Button from "../components/ui/Button";
import { CareerPageModal } from "../components/targets/CareerPageModal";
import { TargetDetail } from "../components/targets/TargetDetail";
import { TargetImportModal } from "../components/targets/TargetImportModal";
import { TargetsFiltersPanel } from "../components/targets/TargetsFiltersPanel";
import { TargetsListPanel } from "../components/targets/TargetsListPanel";
import { useTargetsPageController } from "../components/targets/useTargetsPageController";

export default function Targets() {
  const {
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
    toggleEnabled,
    openCreateCareerPage,
    openEditCareerPage,
    submitCareerPage,
    requestCareerPageDelete,
    deleteCareerPageById,
    setPriorityClass,
    setVendor,
    setStatus,
    closeCareerPageModal,
    careerPageDeleting,
    careerPageSaving,
  } = useTargetsPageController();

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
          onPriorityChange={setPriorityClass}
          onVendorChange={setVendor}
          onStatusChange={setStatus}
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
          onToggleEnabled={toggleEnabled}
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
              deletingCareerPage={careerPageDeleting}
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
        saving={careerPageSaving}
        deleting={careerPageDeleting}
        onClose={closeCareerPageModal}
        onSave={submitCareerPage}
        onDelete={
          careerPageDraft.id
            ? (draft) => {
                const confirmed = window.confirm(
                  `Delete the career page target for ${draft.companyName || draft.url}?`
                );
                if (confirmed) {
                  deleteCareerPageById(draft.id!);
                }
              }
            : undefined
        }
      />
    </div>
  );
}
