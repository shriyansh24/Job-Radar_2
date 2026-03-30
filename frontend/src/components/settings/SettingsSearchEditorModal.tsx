import { CheckCircle } from "@phosphor-icons/react";
import Button from "../ui/Button";
import Input from "../ui/Input";
import Modal from "../ui/Modal";
import Textarea from "../ui/Textarea";

type SearchEditorState = {
  id: string | null;
  name: string;
  filtersText: string;
  alertEnabled: boolean;
};

type SettingsSearchEditorModalProps = {
  open: boolean;
  searchEditor: SearchEditorState;
  saving: boolean;
  onClose: () => void;
  onNameChange: (value: string) => void;
  onFiltersChange: (value: string) => void;
  onAlertEnabledChange: (value: boolean) => void;
  onSave: () => void;
};

function SettingsSearchEditorModal({
  open,
  searchEditor,
  saving,
  onClose,
  onNameChange,
  onFiltersChange,
  onAlertEnabledChange,
  onSave,
}: SettingsSearchEditorModalProps) {
  return (
    <Modal
      open={open}
      onClose={onClose}
      title={searchEditor.id ? "Edit saved search" : "Create saved search"}
      size="lg"
      className="!rounded-none !border-2 !border-[var(--color-text-primary)] !bg-[var(--color-bg-secondary)] !shadow-none"
    >
      <div className="space-y-4">
        <Input
          label="Name"
          value={searchEditor.name}
          onChange={(event) => onNameChange(event.target.value)}
          placeholder="Frontend roles in New York"
        />
        <Textarea
          label="Filters JSON"
          value={searchEditor.filtersText}
          onChange={(event) => onFiltersChange(event.target.value)}
          className="min-h-[220px] font-mono text-sm"
        />
        <label className="flex items-center gap-2 text-sm text-muted-foreground">
          <input
            type="checkbox"
            checked={searchEditor.alertEnabled}
            onChange={(event) => onAlertEnabledChange(event.target.checked)}
            className="size-4 rounded-none border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-secondary)] accent-[var(--color-accent-primary)]"
          />
          Alert when this search changes
        </label>
        <div className="flex justify-end gap-2">
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button
            onClick={onSave}
            loading={saving}
            icon={<CheckCircle size={16} weight="bold" />}
          >
            Save search
          </Button>
        </div>
      </div>
    </Modal>
  );
}

export { SettingsSearchEditorModal };
export type { SearchEditorState, SettingsSearchEditorModalProps };
