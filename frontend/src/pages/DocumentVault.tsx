import { FileText, Scroll } from "@phosphor-icons/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useCallback, useMemo, useState } from "react";
import { useDropzone } from "react-dropzone";
import type { CoverLetterResult } from "../api/copilot";
import { resumeApi, type ResumeVersion } from "../api/resume";
import { vaultApi } from "../api/vault";
import { MetricStrip } from "../components/system/MetricStrip";
import { PageHeader } from "../components/system/PageHeader";
import { SplitWorkspace } from "../components/system/SplitWorkspace";
import { StateBlock } from "../components/system/StateBlock";
import { Surface } from "../components/system/Surface";
import Button from "../components/ui/Button";
import EmptyState from "../components/ui/EmptyState";
import Input from "../components/ui/Input";
import Modal from "../components/ui/Modal";
import { SkeletonCard } from "../components/ui/Skeleton";
import Tabs from "../components/ui/Tabs";
import Textarea from "../components/ui/Textarea";
import { toast } from "../components/ui/toastService";
import { VaultCoverLetterCard, VaultResumeCard, VaultUploadSurface } from "../components/vault/VaultPanels";

const TABS = [
  { id: "resumes", label: "Resumes", icon: <FileText size={14} weight="bold" /> },
  { id: "cover-letters", label: "Cover Letters", icon: <Scroll size={14} weight="bold" /> },
] as const;

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
      toast("success", "Resume uploaded");
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
        hint: "Stored resumes.",
        icon: <FileText size={18} weight="bold" />,
      },
      {
        key: "letters",
        label: "Cover letters",
        value: `${coverLetters?.length ?? 0}`,
        hint: "Saved letter drafts.",
        icon: <Scroll size={18} weight="bold" />,
      },
      {
        key: "editing",
        label: "Editor state",
        value: editingItem ? "Open" : "Idle",
        hint: "Modal state.",
        icon: <FileText size={18} weight="bold" />,
      },
      {
        key: "uploads",
        label: "Upload state",
        value: uploadMutation.isPending ? "Running" : "Ready",
        hint: "Upload readiness.",
        icon: <FileText size={18} weight="bold" />,
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
        description="Store source documents, cover letters, and resume variants in one place."
      />

      <MetricStrip items={metrics} />

      <Tabs tabs={TABS.map((tab) => ({ ...tab }))} activeTab={activeTab} onChange={setActiveTab} />

      {activeTab === "resumes" ? (
        <SplitWorkspace
          primary={
            <div className="space-y-6">
              <VaultUploadSurface
                getRootProps={getRootProps as unknown as () => Record<string, unknown>}
                getInputProps={getInputProps as unknown as () => Record<string, unknown>}
                isDragActive={isDragActive}
                uploading={uploadMutation.isPending}
              />

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
                    title="No resumes"
                    description="Upload a resume to start the vault."
                  />
                </Surface>
              ) : (
                <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                  {resumes.map((resume) => (
                    <VaultResumeCard
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
                description="Keep source material stable while downstream surfaces generate variants."
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
                  title="No cover letters"
                  description="Generate a letter in Copilot and it will appear here."
                />
              </Surface>
            ) : (
              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                {coverLetters.map((letter) => (
                  <VaultCoverLetterCard
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
                description="Letter drafts stay editable here before reuse."
              />
            </div>
          }
        />
      ) : null}

      <Modal
        open={!!previewResume}
        onClose={() => setPreviewResume(null)}
        title={previewResume?.filename ?? "Resume preview"}
        size="lg"
      >
        {previewResume?.parsed_text ? (
          <pre className="whitespace-pre-wrap font-mono text-sm text-text-primary">{previewResume.parsed_text}</pre>
        ) : (
          <div className="flex items-center justify-center gap-3 py-8 text-text-muted">
            <FileText size={20} weight="bold" />
            <span className="text-sm">No parsed text available yet.</span>
          </div>
        )}
      </Modal>

      <Modal
        open={!!editingItem}
        onClose={closeEditor}
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
              Save
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
