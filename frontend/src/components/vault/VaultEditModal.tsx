import type { CoverLetterResult } from "../../api/copilot";
import type { ResumeVersion } from "../../api/resume";
import Button from "../ui/Button";
import Input from "../ui/Input";
import Modal from "../ui/Modal";
import Textarea from "../ui/Textarea";

type VaultEditingItem =
  | { kind: "resume"; item: ResumeVersion }
  | { kind: "cover-letter"; item: CoverLetterResult }
  | null;

export function VaultEditModal({
  editingItem,
  editValue,
  editorPending,
  onClose,
  onEditValueChange,
  onSave,
}: {
  editingItem: VaultEditingItem;
  editValue: string;
  editorPending: boolean;
  onClose: () => void;
  onEditValueChange: (value: string) => void;
  onSave: () => void;
}) {
  return (
    <Modal
      open={!!editingItem}
      onClose={onClose}
      title={editingItem?.kind === "resume" ? "Edit resume label" : "Edit cover letter"}
      size="lg"
    >
      <div className="space-y-4">
        <p className="text-sm text-text-secondary">
          {editingItem?.kind === "resume" ? "Rename the resume label." : "Update the saved cover letter."}
        </p>
        {editingItem?.kind === "resume" ? (
          <Input
            label="Label"
            aria-label="Resume label"
            value={editValue}
            onChange={(event) => onEditValueChange(event.target.value)}
            placeholder="Optional label"
          />
        ) : (
          <Textarea
            label="Content"
            aria-label="Cover letter content"
            value={editValue}
            onChange={(event) => onEditValueChange(event.target.value)}
            className="min-h-[240px]"
          />
        )}
        <div className="flex items-center justify-end gap-2 pt-2">
          <Button variant="secondary" onClick={onClose} disabled={editorPending}>
            Cancel
          </Button>
          <Button onClick={onSave} loading={editorPending}>
            Save
          </Button>
        </div>
      </div>
    </Modal>
  );
}
