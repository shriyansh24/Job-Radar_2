import {
  Briefcase,
  Clock,
  Eye,
  FileText,
  PencilSimple,
  Scroll,
  Trash,
  UploadSimple,
} from "@phosphor-icons/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { format } from "date-fns";
import { useCallback, useMemo, useState } from "react";
import { useDropzone } from "react-dropzone";
import type { CoverLetterResult } from "../api/copilot";
import { resumeApi, type ResumeVersion } from "../api/resume";
import { vaultApi } from "../api/vault";
import { MetricStrip } from "../components/system/MetricStrip";
import { PageHeader } from "../components/system/PageHeader";
import { SectionHeader } from "../components/system/SectionHeader";
import { SplitWorkspace } from "../components/system/SplitWorkspace";
import { StateBlock } from "../components/system/StateBlock";
import { Surface } from "../components/system/Surface";
import Badge from "../components/ui/Badge";
import Button from "../components/ui/Button";
import EmptyState from "../components/ui/EmptyState";
import Input from "../components/ui/Input";
import Modal from "../components/ui/Modal";
import { SkeletonCard } from "../components/ui/Skeleton";
import Tabs from "../components/ui/Tabs";
import Textarea from "../components/ui/Textarea";
import { toast } from "../components/ui/toastService";

const TABS = [
  { id: "resumes", label: "Resumes", icon: <FileText size={14} weight="bold" /> },
  { id: "cover-letters", label: "Cover Letters", icon: <Scroll size={14} weight="bold" /> },
] as const;

function ResumeCard({
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

function CoverLetterCard({
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

export default function DocumentVault() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState("resumes");
  const [previewResume, setPreviewResume] = useState<ResumeVersion | null>(null);
  const [editingItem, setEditingItem] = useState<
    | { kind: "resume"; item: ResumeVersion }
    | { kind: "cover-letter"; item: CoverLetterResult }
    | null
  >(null);
  const [editValue, setEditValue] = useState("");

  const { data: resumes, isLoading: resumesLoading } = useQuery({
    queryKey: ["vault-resumes"],
    queryFn: () => vaultApi.listResumes().then((response) => response.data),
  });

  const { data: coverLetters, isLoading: lettersLoading } = useQuery({
    queryKey: ["vault-cover-letters"],
    queryFn: () => vaultApi.listCoverLetters().then((response) => response.data),
  });

  const uploadMutation = useMutation({
    mutationFn: (file: File) => resumeApi.upload(file),
    onSuccess: () => {
      toast("success", "Resume uploaded successfully");
      queryClient.invalidateQueries({ queryKey: ["vault-resumes"] });
    },
    onError: () => toast("error", "Failed to upload resume"),
  });

  const deleteResumeMutation = useMutation({
    mutationFn: (id: string) => vaultApi.deleteResume(id),
    onSuccess: () => {
      toast("success", "Resume deleted");
      queryClient.invalidateQueries({ queryKey: ["vault-resumes"] });
    },
    onError: () => toast("error", "Failed to delete resume"),
  });

  const deleteCoverLetterMutation = useMutation({
    mutationFn: (id: string) => vaultApi.deleteCoverLetter(id),
    onSuccess: () => {
      toast("success", "Cover letter deleted");
      queryClient.invalidateQueries({ queryKey: ["vault-cover-letters"] });
    },
    onError: () => toast("error", "Failed to delete cover letter"),
  });

  const updateResumeMutation = useMutation({
    mutationFn: ({ id, label }: { id: string; label: string }) => vaultApi.updateResume(id, label),
    onSuccess: () => {
      toast("success", "Resume updated");
      queryClient.invalidateQueries({ queryKey: ["vault-resumes"] });
      closeEditor();
    },
    onError: () => toast("error", "Failed to update resume"),
  });

  const updateCoverLetterMutation = useMutation({
    mutationFn: ({ id, content }: { id: string; content: string }) =>
      vaultApi.updateCoverLetter(id, content),
    onSuccess: () => {
      toast("success", "Cover letter updated");
      queryClient.invalidateQueries({ queryKey: ["vault-cover-letters"] });
      closeEditor();
    },
    onError: () => toast("error", "Failed to update cover letter"),
  });

  const onDrop = useCallback(
    (accepted: File[]) => {
      const file = accepted[0];
      if (file) uploadMutation.mutate(file);
    },
    [uploadMutation]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
    },
    maxFiles: 1,
  });

  function closeEditor() {
    setEditingItem(null);
    setEditValue("");
  }

  function handleEditResume(resume: ResumeVersion) {
    setEditingItem({ kind: "resume", item: resume });
    setEditValue(resume.label ?? "");
  }

  function handleEditCoverLetter(letter: CoverLetterResult) {
    setEditingItem({ kind: "cover-letter", item: letter });
    setEditValue(letter.content);
  }

  function handleSaveEdit() {
    if (!editingItem) return;

    if (editingItem.kind === "resume") {
      updateResumeMutation.mutate({
        id: editingItem.item.id,
        label: editValue.trim(),
      });
      return;
    }

    updateCoverLetterMutation.mutate({
      id: editingItem.item.id,
      content: editValue,
    });
  }

  const editorPending = updateResumeMutation.isPending || updateCoverLetterMutation.isPending;

  const metrics = useMemo(
    () => [
      {
        key: "resumes",
        label: "Resumes",
        value: `${resumes?.length ?? 0}`,
        hint: "Resume documents currently stored in the vault.",
        icon: <FileText size={18} weight="bold" />,
      },
      {
        key: "letters",
        label: "Cover letters",
        value: `${coverLetters?.length ?? 0}`,
        hint: "Saved letter drafts available for reuse and editing.",
        icon: <Scroll size={18} weight="bold" />,
      },
      {
        key: "editing",
        label: "Editor state",
        value: editingItem ? "Open" : "Idle",
        hint: "Whether the vault editor modal is currently active.",
        icon: <PencilSimple size={18} weight="bold" />,
      },
      {
        key: "uploads",
        label: "Upload state",
        value: uploadMutation.isPending ? "Running" : "Ready",
        hint: "Current readiness of the vault upload surface.",
        icon: <UploadSimple size={18} weight="bold" />,
        tone: uploadMutation.isPending ? ("warning" as const) : ("default" as const),
      },
    ],
    [coverLetters?.length, editingItem, resumes?.length, uploadMutation.isPending]
  );

  return (
    <div className="space-y-6">
      <PageHeader
        className="hero-panel"
        eyebrow="Prepare"
        title="Document Vault"
        description="Keep source documents, cover letters, and resume variants in one place for easy reuse."
      />

      <MetricStrip items={metrics} />

      <Tabs tabs={TABS.map((tab) => ({ ...tab }))} activeTab={activeTab} onChange={setActiveTab} />

      {activeTab === "resumes" ? (
        <SplitWorkspace
          primary={
            <div className="space-y-6">
              <Surface tone="default" padding="lg" radius="xl" className="hero-panel">
                <SectionHeader
                  title="Resume intake"
                  description="A drop surface for current source documents before they move into tailoring, review, and outbound application work."
                />
                <button
                  type="button"
                  {...getRootProps()}
                className="hero-panel mt-5 flex w-full flex-col items-center justify-center border-2 border-dashed border-border px-6 py-12 text-center transition-colors"
                >
                  <input {...getInputProps()} />
                  <UploadSimple size={34} weight="bold" />
                  <p className="mt-4 text-lg font-black uppercase tracking-[-0.05em] text-text-primary">
                    {isDragActive ? "Drop your resume here" : "Drag & drop a resume, or click to browse"}
                  </p>
                  <p className="mt-2 text-sm text-text-secondary">PDF or DOCX, max 10MB</p>
                  {uploadMutation.isPending ? <p className="mt-3 text-sm text-accent-primary">Uploading...</p> : null}
                </button>
              </Surface>

              {resumesLoading ? (
                <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                  {Array.from({ length: 3 }).map((_, index) => (
                    <SkeletonCard key={index} />
                  ))}
                </div>
              ) : !resumes || resumes.length === 0 ? (
                <Surface tone="default" padding="lg" radius="xl" className="brutal-panel">
                  <EmptyState
                    icon={<FileText size={40} weight="bold" />}
                    title="No resumes yet"
                    description="Upload your first resume to start building your document vault"
                  />
                </Surface>
              ) : (
                <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                  {resumes.map((resume: ResumeVersion) => (
                    <ResumeCard
                      key={resume.id}
                      resume={resume}
                      onPreview={() => setPreviewResume(resume)}
                      onEdit={() => handleEditResume(resume)}
                      onDelete={() => deleteResumeMutation.mutate(resume.id)}
                    />
                  ))}
                </div>
              )}
            </div>
          }
          secondary={
            <div className="space-y-4">
              <StateBlock
                tone="neutral"
                icon={<FileText size={18} weight="bold" />}
                title="Vault role"
                description="This is the long-term document shelf. Use it to keep source materials stable while downstream surfaces generate variants."
              />
            </div>
          }
        />
      ) : null}

      {activeTab === "cover-letters" ? (
        <SplitWorkspace
          primary={
            lettersLoading ? (
              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                {Array.from({ length: 3 }).map((_, index) => (
                  <SkeletonCard key={index} />
                ))}
              </div>
            ) : !coverLetters || coverLetters.length === 0 ? (
              <Surface tone="default" padding="lg" radius="xl" className="hero-panel">
                <EmptyState
                  icon={<Scroll size={40} weight="bold" />}
                  title="No cover letters yet"
                  description="Generate cover letters from the Copilot page and they will appear here"
                />
              </Surface>
            ) : (
              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                {coverLetters.map((letter: CoverLetterResult) => (
                  <CoverLetterCard
                    key={letter.id}
                    letter={letter}
                    onEdit={() => handleEditCoverLetter(letter)}
                    onDelete={() => deleteCoverLetterMutation.mutate(letter.id)}
                  />
                ))}
              </div>
            )
          }
          secondary={
            <div className="space-y-4">
              <StateBlock
                tone="warning"
                icon={<Scroll size={18} weight="bold" />}
                title="Draft behavior"
                description="Letter drafts are intentionally editable here so Copilot output can be cleaned up before reuse."
              />
            </div>
          }
        />
      ) : null}

      <Modal
        open={!!previewResume}
        onClose={() => setPreviewResume(null)}
        title={previewResume?.filename ?? "Resume Preview"}
        size="lg"
      >
        {previewResume?.parsed_text ? (
          <pre className="whitespace-pre-wrap font-mono text-sm text-text-primary">
            {previewResume.parsed_text}
          </pre>
        ) : (
          <div className="flex items-center justify-center gap-3 py-8 text-text-muted">
            <FileText size={20} weight="bold" />
            <span className="text-sm">No text has been extracted from this resume yet.</span>
          </div>
        )}
      </Modal>

      <Modal
        open={!!editingItem}
        onClose={closeEditor}
        title={editingItem?.kind === "resume" ? "Edit Resume Label" : "Edit Cover Letter"}
        size="lg"
      >
        <div className="space-y-4">
          <p className="text-sm text-text-secondary">
            {editingItem?.kind === "resume"
              ? "Rename how this resume version appears in the vault."
              : "Update the saved cover letter text."}
          </p>
          {editingItem?.kind === "resume" ? (
            <Input
              label="Label"
              aria-label="Resume label"
              value={editValue}
              onChange={(event) => setEditValue(event.target.value)}
              placeholder="Optional label"
            />
          ) : (
            <Textarea
              label="Content"
              aria-label="Cover letter content"
              value={editValue}
              onChange={(event) => setEditValue(event.target.value)}
              className="min-h-[240px]"
            />
          )}
          <div className="flex items-center justify-end gap-2 pt-2">
            <Button variant="secondary" onClick={closeEditor} disabled={editorPending}>
              Cancel
            </Button>
            <Button onClick={handleSaveEdit} loading={editorPending}>
              Save changes
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
