import { ArrowClockwise, DownloadSimple, Trash, UploadSimple, Warning } from "@phosphor-icons/react";
import { useRef, type ChangeEvent } from "react";
import Button from "../ui/Button";
import Modal from "../ui/Modal";
import { Surface } from "../system/Surface";

export function AdminMaintenanceActionsPanel({
  onReindex,
  reindexPending,
  onExport,
  exportPending,
  onImportFile,
  importPending,
  clearDataOpen,
  onRequestClearData,
  onCancelClearData,
  onConfirmClearData,
  clearDataPending,
}: {
  onReindex: () => void;
  reindexPending: boolean;
  onExport: () => void;
  exportPending: boolean;
  onImportFile: (event: ChangeEvent<HTMLInputElement>) => void;
  importPending: boolean;
  clearDataOpen: boolean;
  onRequestClearData: () => void;
  onCancelClearData: () => void;
  onConfirmClearData: () => void;
  clearDataPending: boolean;
}) {
  const fileInputRef = useRef<HTMLInputElement>(null);

  return (
    <Surface className="border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-secondary)]">
      <div className="space-y-4">
        <div>
          <div className="text-sm font-bold uppercase tracking-[0.2em]">Actions</div>
          <p className="mt-1 text-sm text-text-secondary">Maintenance operations for indexing, portability, and destructive resets.</p>
        </div>
        <div className="flex flex-wrap gap-3">
          <Button variant="secondary" icon={<ArrowClockwise size={14} weight="bold" />} loading={reindexPending} onClick={onReindex}>
            Reindex FTS
          </Button>
          <Button variant="danger" icon={<Trash size={14} weight="bold" />} loading={clearDataPending} onClick={onRequestClearData}>
            Clear Data
          </Button>
          <Button variant="secondary" icon={<DownloadSimple size={14} weight="bold" />} loading={exportPending} onClick={onExport}>
            Export Data
          </Button>
          <Button
            variant="secondary"
            icon={<UploadSimple size={14} weight="bold" />}
            loading={importPending}
            onClick={() => fileInputRef.current?.click()}
          >
            Import Data
          </Button>
          <input ref={fileInputRef} type="file" accept=".json" className="hidden" onChange={onImportFile} />
        </div>
        <Modal open={clearDataOpen} onClose={onCancelClearData} title="Clear data" size="sm">
          <div className="space-y-4">
            <div className="flex items-start gap-3 border-2 border-border bg-[var(--color-bg-tertiary)] p-4">
              <Warning size={18} weight="bold" className="mt-0.5 shrink-0 text-[var(--color-accent-danger)]" />
              <p className="text-sm leading-6 text-text-secondary">
                This will call the live admin clear-data endpoint and remove stored application data. Use import/export if you need a backup first.
              </p>
            </div>
            <div className="flex flex-wrap gap-3">
              <Button variant="secondary" onClick={onCancelClearData}>
                Cancel
              </Button>
              <Button
                variant="danger"
                loading={clearDataPending}
                onClick={onConfirmClearData}
                icon={<Trash size={14} weight="bold" />}
              >
                Clear Data
              </Button>
            </div>
          </div>
        </Modal>
      </div>
    </Surface>
  );
}
