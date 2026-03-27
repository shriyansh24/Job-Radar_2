import { ArrowClockwise, DownloadSimple, UploadSimple } from "@phosphor-icons/react";
import { useRef, type ChangeEvent } from "react";
import Button from "../ui/Button";
import { Surface } from "../system/Surface";

export function AdminMaintenanceActionsPanel({
  onReindex,
  reindexPending,
  onExport,
  exportPending,
  onImportFile,
  importPending,
}: {
  onReindex: () => void;
  reindexPending: boolean;
  onExport: () => void;
  exportPending: boolean;
  onImportFile: (event: ChangeEvent<HTMLInputElement>) => void;
  importPending: boolean;
}) {
  const fileInputRef = useRef<HTMLInputElement>(null);

  return (
    <Surface className="border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-secondary)]">
      <div className="space-y-4">
        <div>
          <div className="text-sm font-bold uppercase tracking-[0.2em]">Actions</div>
          <p className="mt-1 text-sm text-text-secondary">Maintenance operations for indexing and data portability.</p>
        </div>
        <div className="flex flex-wrap gap-3">
          <Button variant="secondary" icon={<ArrowClockwise size={14} weight="bold" />} loading={reindexPending} onClick={onReindex}>
            Reindex FTS
          </Button>
          <Button variant="secondary" icon={<ArrowClockwise size={14} weight="bold" />} loading={reindexPending} onClick={onReindex}>
            Reindex Search
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
      </div>
    </Surface>
  );
}
