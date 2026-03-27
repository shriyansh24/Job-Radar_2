import { Database, DownloadSimple, Trash, WarningCircle } from "@phosphor-icons/react";
import Button from "../ui/Button";
import Input from "../ui/Input";
import { SettingsSection } from "../system/SettingsSection";

type SettingsDataSectionProps = {
  clearConfirm: string;
  deleteConfirm: string;
  onClearConfirmChange: (value: string) => void;
  onDeleteConfirmChange: (value: string) => void;
  onExport: () => void;
  onClear: () => void;
  onDelete: () => void;
  clearReady: boolean;
  deleteReady: boolean;
  clearPending: boolean;
  deletePending: boolean;
};

function SettingsDataSection({
  clearConfirm,
  deleteConfirm,
  onClearConfirmChange,
  onDeleteConfirmChange,
  onExport,
  onClear,
  onDelete,
  clearReady,
  deleteReady,
  clearPending,
  deletePending,
}: SettingsDataSectionProps) {
  return (
    <div className="space-y-6">
      <SettingsSection title="Data" description="Export or clear workspace data." className="border-2 border-border bg-card shadow-hard-xl">
        <div className="space-y-6">
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <Database size={16} weight="bold" className="text-muted-foreground" />
              <h4 className="text-sm font-bold uppercase tracking-[0.12em] text-foreground">Export</h4>
            </div>
            <p className="text-sm text-muted-foreground">Download workspace data as JSON.</p>
            <Button variant="secondary" onClick={onExport} icon={<DownloadSimple size={16} weight="bold" />}>
              Export data
            </Button>
          </div>

          <div className="space-y-3 border-t border-border pt-6">
            <div className="flex items-center gap-2">
              <WarningCircle size={16} weight="bold" className="text-accent-danger" />
              <h4 className="text-sm font-bold uppercase tracking-[0.12em] text-foreground">Clear workspace</h4>
            </div>
            <p className="text-sm text-muted-foreground">Remove workspace data. This cannot be undone.</p>
            <Input
              label='Type "clear" to enable the action'
              value={clearConfirm}
              onChange={(event) => onClearConfirmChange(event.target.value)}
              placeholder="clear"
            />
            <Button
              variant="danger"
              onClick={onClear}
              loading={clearPending}
              icon={<WarningCircle size={16} weight="bold" />}
              disabled={!clearReady}
            >
              Clear data
            </Button>
          </div>
        </div>
      </SettingsSection>

      <SettingsSection title="Delete account" description="Remove the current account permanently." className="border-2 border-border bg-card shadow-hard-xl">
        <div className="space-y-4">
          <p className="text-sm text-muted-foreground">This removes account access permanently.</p>
          <Input
            label='Type "delete" to enable the action'
            value={deleteConfirm}
            onChange={(event) => onDeleteConfirmChange(event.target.value)}
            placeholder="delete"
          />
          <Button variant="danger" onClick={onDelete} loading={deletePending} disabled={!deleteReady} icon={<Trash size={16} weight="bold" />}>
            Delete account
          </Button>
        </div>
      </SettingsSection>
    </div>
  );
}

export { SettingsDataSection };
export type { SettingsDataSectionProps };
