import { Briefcase, Clock, Eye, FileText, PencilSimple, Trash, UploadSimple } from "@phosphor-icons/react";
import { format } from "date-fns";
import { useState } from "react";
import type { DropzoneInputProps, DropzoneRootProps } from "react-dropzone";
import type { CoverLetterResult } from "../../api/copilot";
import { type ResumeVersion } from "../../api/resume";
import { Surface } from "../system/Surface";
import Badge from "../ui/Badge";
import Button from "../ui/Button";

export function VaultResumeCard({
  resume,
  onPreview,
  onEdit,
  onDelete,
}: {
  resume: ResumeVersion;
  onPreview: () => void;
  onEdit: () => void;
  onDelete: () => void;
}) {
  const [confirmDelete, setConfirmDelete] = useState(false);

  return (
    <Surface tone="default" padding="lg" radius="xl" className="brutal-panel space-y-4">
      <div className="flex items-start gap-3">
        <div className="hero-panel flex size-12 shrink-0 items-center justify-center">
          <FileText size={22} weight="bold" />
        </div>
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-semibold text-text-primary">{resume.filename}</p>
          <p className="mt-2 flex items-center gap-1 text-xs text-text-muted">
            <Clock size={12} weight="bold" />
            {format(new Date(resume.created_at), "PP")}
          </p>
        </div>
      </div>

      <div className="flex flex-wrap gap-2 border-t-2 border-border pt-4">
        <Button variant="ghost" size="sm" icon={<Eye size={14} weight="bold" />} onClick={onPreview}>
          Preview
        </Button>
        <Button variant="ghost" size="sm" icon={<PencilSimple size={14} weight="bold" />} onClick={onEdit}>
          Edit
        </Button>
        {confirmDelete ? (
          <div className="ml-auto flex items-center gap-1.5">
            <span className="text-xs text-text-muted">Delete?</span>
            <Button variant="danger" size="sm" onClick={onDelete}>
              Yes
            </Button>
            <Button variant="secondary" size="sm" onClick={() => setConfirmDelete(false)}>
              No
            </Button>
          </div>
        ) : (
          <Button
            variant="ghost"
            size="sm"
            icon={<Trash size={14} weight="bold" />}
            className="ml-auto text-accent-danger hover:text-accent-danger"
            onClick={() => setConfirmDelete(true)}
          >
            Delete
          </Button>
        )}
      </div>
    </Surface>
  );
}

export function VaultCoverLetterCard({
  letter,
  onEdit,
  onDelete,
}: {
  letter: CoverLetterResult;
  onEdit: () => void;
  onDelete: () => void;
}) {
  const [confirmDelete, setConfirmDelete] = useState(false);

  return (
    <Surface tone="default" padding="lg" radius="xl" className="brutal-panel space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="info">{letter.style ?? "Cover Letter"}</Badge>
          <span className="flex items-center gap-1 text-xs text-text-muted">
            <Briefcase size={10} weight="bold" />
            {letter.job_id ? `${letter.job_id.slice(0, 8)}...` : "General"}
          </span>
        </div>
        <p className="text-xs text-text-muted">{format(new Date(letter.created_at), "PP")}</p>
      </div>

      <p className="line-clamp-5 text-sm leading-6 text-text-secondary">{letter.content}</p>

      <div className="flex flex-wrap justify-end gap-2 border-t-2 border-border pt-4">
        <Button variant="ghost" size="sm" icon={<PencilSimple size={14} weight="bold" />} onClick={onEdit}>
          Edit
        </Button>
        {confirmDelete ? (
          <div className="flex items-center gap-1.5">
            <span className="text-xs text-text-muted">Delete?</span>
            <Button variant="danger" size="sm" onClick={onDelete}>
              Yes
            </Button>
            <Button variant="secondary" size="sm" onClick={() => setConfirmDelete(false)}>
              No
            </Button>
          </div>
        ) : (
          <Button
            variant="ghost"
            size="sm"
            icon={<Trash size={14} weight="bold" />}
            className="text-accent-danger hover:text-accent-danger"
            onClick={() => setConfirmDelete(true)}
          >
            Delete
          </Button>
        )}
      </div>
    </Surface>
  );
}

export function VaultUploadSurface({
  getRootProps,
  getInputProps,
  isDragActive,
  uploading,
}: {
  getRootProps: () => DropzoneRootProps;
  getInputProps: () => DropzoneInputProps;
  isDragActive: boolean;
  uploading: boolean;
}) {
  return (
    <Surface tone="default" padding="lg" radius="xl" className="hero-panel">
      <div className="space-y-6">
        <div>
          <div className="text-sm font-bold uppercase tracking-[0.18em] text-text-primary">Upload</div>
          <p className="mt-2 text-sm leading-6 text-text-secondary">Add a resume before it moves into the vault.</p>
        </div>
        <button
          type="button"
          {...getRootProps()}
          className="hero-panel flex w-full flex-col items-center justify-center border-2 border-dashed border-border px-6 py-12 text-center transition-colors"
        >
          <input {...getInputProps()} />
          <UploadSimple size={34} weight="bold" />
          <p className="mt-4 text-lg font-black uppercase tracking-[-0.05em] text-text-primary">
            {isDragActive ? "Drop the file here" : "Drag and drop a resume"}
          </p>
          <p className="mt-2 text-sm text-text-secondary">PDF or DOCX</p>
          {uploading ? <p className="mt-3 text-sm text-accent-primary">Uploading...</p> : null}
        </button>
      </div>
    </Surface>
  );
}
