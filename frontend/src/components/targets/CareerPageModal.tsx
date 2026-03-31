import { CheckCircle, Trash } from "@phosphor-icons/react";
import { useEffect, useState } from "react";
import { getSafeExternalUrl } from "../../lib/utils";
import Modal from "../ui/Modal";
import Input from "../ui/Input";
import Toggle from "../ui/Toggle";
import Button from "../ui/Button";

type CareerPageDraft = {
  id: string | null;
  url: string;
  companyName: string;
  enabled: boolean;
  canDelete: boolean;
  deleteBlockedReason: string | null;
};

type CareerPageModalProps = {
  open: boolean;
  draft: CareerPageDraft;
  saving: boolean;
  deleting?: boolean;
  onClose: () => void;
  onSave: (draft: CareerPageDraft) => void;
  onDelete?: (draft: CareerPageDraft) => void;
};

function CareerPageModal({
  open,
  draft,
  saving,
  deleting = false,
  onClose,
  onSave,
  onDelete,
}: CareerPageModalProps) {
  const [localDraft, setLocalDraft] = useState(draft);
  const [urlError, setUrlError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setLocalDraft(draft);
      setUrlError(null);
    }
  }, [draft, open]);

  const isEditing = Boolean(localDraft.id);
  const trimmedUrl = localDraft.url.trim();
  const normalizedUrl = trimmedUrl ? getSafeExternalUrl(trimmedUrl) : null;

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={isEditing ? "Edit career page" : "Add career page"}
      size="lg"
    >
      <form
        className="space-y-5"
        onSubmit={(event) => {
          event.preventDefault();
          if (!normalizedUrl) {
            setUrlError('Career page URL must be a valid "http://" or "https://" URL');
            return;
          }
          onSave({
            ...localDraft,
            url: normalizedUrl,
            companyName: localDraft.companyName.trim(),
          });
        }}
      >
        <Input
          label="Career page URL"
          type="url"
          value={localDraft.url}
          error={urlError ?? undefined}
          onChange={(event) => {
            setUrlError(null);
            setLocalDraft((current) => ({ ...current, url: event.target.value }));
          }}
          placeholder="https://company.example/careers"
        />
        <Input
          label="Company name"
          value={localDraft.companyName}
          onChange={(event) =>
            setLocalDraft((current) => ({ ...current, companyName: event.target.value }))
          }
          placeholder="Acme"
        />
        {isEditing ? (
          <div className="flex items-center justify-between gap-4 border-2 border-border p-4">
            <div>
              <h4 className="text-sm font-bold uppercase tracking-[0.12em] text-foreground">
                Enabled
              </h4>
              <p className="mt-1 text-sm text-muted-foreground">
                Include this career page in scheduled runs.
              </p>
            </div>
            <Toggle
              checked={localDraft.enabled}
              onChange={(enabled) =>
                setLocalDraft((current) => ({ ...current, enabled }))
              }
            />
          </div>
        ) : null}
        <div className="flex flex-wrap justify-between gap-2">
          <div>
            {isEditing && onDelete ? (
              localDraft.canDelete ? (
                <Button
                  type="button"
                  variant="danger"
                  loading={deleting}
                  onClick={() => onDelete(localDraft)}
                  icon={<Trash size={16} weight="bold" />}
                >
                  Delete career page
                </Button>
              ) : (
                <p className="max-w-sm text-sm text-muted-foreground">
                  {localDraft.deleteBlockedReason ??
                    "Delete is unavailable once the target has scrape history."}
                </p>
              )
            ) : null}
          </div>
          <div className="flex gap-2">
            <Button type="button" variant="secondary" onClick={onClose}>
              Cancel
            </Button>
            <Button
              type="submit"
              loading={saving}
              disabled={!trimmedUrl}
              icon={<CheckCircle size={16} weight="bold" />}
            >
              {isEditing ? "Save changes" : "Create career page"}
            </Button>
          </div>
        </div>
      </form>
    </Modal>
  );
}

export { CareerPageModal };
export type { CareerPageDraft, CareerPageModalProps };
