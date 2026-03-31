import { FileText, Scroll } from "@phosphor-icons/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useCallback, useMemo, useState } from "react";
import { useDropzone } from "react-dropzone";
import type { CoverLetterResult } from "../api/copilot";
import { resumeApi, type ResumeVersion } from "../api/resume";
import { vaultApi } from "../api/vault";
import { MetricStrip } from "../components/system/MetricStrip";
import { PageHeader } from "../components/system/PageHeader";
import Tabs from "../components/ui/Tabs";
import { toast } from "../components/ui/toastService";
import { VaultCoverLettersTab } from "../components/vault/VaultCoverLettersTab";
import { VaultEditModal } from "../components/vault/VaultEditModal";
import { VaultPreviewModal } from "../components/vault/VaultPreviewModal";
import { VaultResumesTab } from "../components/vault/VaultResumesTab";

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
        <VaultResumesTab
          resumes={resumes}
          resumesLoading={resumesLoading}
          getRootProps={getRootProps}
          getInputProps={getInputProps}
          isDragActive={isDragActive}
          uploading={uploadMutation.isPending}
          onPreview={setPreviewResume}
          onEdit={handleEditResume}
          onDelete={(resumeId) => deleteResumeMutation.mutate(resumeId)}
        />
      ) : null}

      {activeTab === "cover-letters" ? (
        <VaultCoverLettersTab
          coverLetters={coverLetters}
          lettersLoading={lettersLoading}
          onEdit={handleEditCoverLetter}
          onDelete={(letterId) => deleteCoverLetterMutation.mutate(letterId)}
        />
      ) : null}

      <VaultPreviewModal resume={previewResume} onClose={() => setPreviewResume(null)} />

      <VaultEditModal
        editingItem={editingItem}
        editValue={editValue}
        editorPending={editorPending}
        onClose={closeEditor}
        onEditValueChange={setEditValue}
        onSave={handleSaveEdit}
      />
    </div>
  );
}
