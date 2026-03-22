import {
  Briefcase,
  Clock,
  FileText,
  Eye,
  PencilSimple,
  Scroll,
  Trash,
  UploadSimple,
} from "@phosphor-icons/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { format } from "date-fns";
import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import type { CoverLetterResult } from "../api/copilot";
import { resumeApi, type ResumeVersion } from "../api/resume";
import { vaultApi } from "../api/vault";
import Badge from "../components/ui/Badge";
import Button from "../components/ui/Button";
import Card from "../components/ui/Card";
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
];

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
    <Card hover>
      <div className="flex items-start gap-3">
        <FileText size={24} weight="bold" className="text-accent-primary shrink-0 mt-0.5" />
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium text-text-primary truncate">
            {resume.filename}
          </p>
          <p className="text-xs text-text-muted flex items-center gap-1 mt-1">
            <Clock size={10} weight="bold" />
            {format(new Date(resume.created_at), 'PP')}
          </p>
        </div>
      </div>
      <div className="flex items-center gap-2 mt-3 pt-3 border-t border-border">
        <Button
          variant="ghost"
          size="sm"
          icon={<Eye size={14} weight="bold" />}
          onClick={onPreview}
        >
          Preview
        </Button>
        <Button
          variant="ghost"
          size="sm"
          icon={<PencilSimple size={14} weight="bold" />}
          onClick={onEdit}
        >
          Edit
        </Button>
        {confirmDelete ? (
          <div className="flex items-center gap-1.5 ml-auto">
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
    </Card>
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
    <Card hover>
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <Badge variant="info" size="sm">{letter.style ?? "Cover Letter"}</Badge>
          <span className="text-xs text-text-muted flex items-center gap-1">
            <Briefcase size={10} weight="bold" />
            {letter.job_id ? `${letter.job_id.slice(0, 8)}...` : "General"}
          </span>
        </div>
        <p className="text-xs text-text-muted">
          {format(new Date(letter.created_at), 'PP')}
        </p>
      </div>
      <p className="text-sm text-text-secondary mt-3 line-clamp-4 leading-relaxed">
        {letter.content}
      </p>
      <div className="flex items-center justify-end gap-2 mt-3 pt-3 border-t border-border">
        <Button
          variant="ghost"
          size="sm"
          icon={<PencilSimple size={14} weight="bold" />}
          onClick={onEdit}
        >
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
    </Card>
  );
}

export default function DocumentVault() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState('resumes');
  const [previewResume, setPreviewResume] = useState<ResumeVersion | null>(null);
  const [editingItem, setEditingItem] = useState<
    | { kind: 'resume'; item: ResumeVersion }
    | { kind: 'cover-letter'; item: CoverLetterResult }
    | null
  >(null);
  const [editValue, setEditValue] = useState('');

  // Queries
  const { data: resumes, isLoading: resumesLoading } = useQuery({
    queryKey: ['vault-resumes'],
    queryFn: () => vaultApi.listResumes().then((r) => r.data),
  });

  const { data: coverLetters, isLoading: lettersLoading } = useQuery({
    queryKey: ['vault-cover-letters'],
    queryFn: () => vaultApi.listCoverLetters().then((r) => r.data),
  });

  // Mutations
  const uploadMutation = useMutation({
    mutationFn: (file: File) => resumeApi.upload(file),
    onSuccess: () => {
      toast('success', 'Resume uploaded successfully');
      queryClient.invalidateQueries({ queryKey: ['vault-resumes'] });
    },
    onError: () => toast('error', 'Failed to upload resume'),
  });

  const deleteResumeMutation = useMutation({
    mutationFn: (id: string) => vaultApi.deleteResume(id),
    onSuccess: () => {
      toast('success', 'Resume deleted');
      queryClient.invalidateQueries({ queryKey: ['vault-resumes'] });
    },
    onError: () => toast('error', 'Failed to delete resume'),
  });

  const deleteCoverLetterMutation = useMutation({
    mutationFn: (id: string) => vaultApi.deleteCoverLetter(id),
    onSuccess: () => {
      toast('success', 'Cover letter deleted');
      queryClient.invalidateQueries({ queryKey: ['vault-cover-letters'] });
    },
    onError: () => toast('error', 'Failed to delete cover letter'),
  });

  const updateResumeMutation = useMutation({
    mutationFn: ({ id, label }: { id: string; label: string }) =>
      vaultApi.updateResume(id, label),
    onSuccess: () => {
      toast('success', 'Resume updated');
      queryClient.invalidateQueries({ queryKey: ['vault-resumes'] });
      closeEditor();
    },
    onError: () => toast('error', 'Failed to update resume'),
  });

  const updateCoverLetterMutation = useMutation({
    mutationFn: ({ id, content }: { id: string; content: string }) =>
      vaultApi.updateCoverLetter(id, content),
    onSuccess: () => {
      toast('success', 'Cover letter updated');
      queryClient.invalidateQueries({ queryKey: ['vault-cover-letters'] });
      closeEditor();
    },
    onError: () => toast('error', 'Failed to update cover letter'),
  });

  // Dropzone
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
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    },
    maxFiles: 1,
  });

  function closeEditor() {
    setEditingItem(null);
    setEditValue('');
  }

  function handleEditResume(resume: ResumeVersion) {
    setEditingItem({ kind: 'resume', item: resume });
    setEditValue(resume.label ?? '');
  }

  function handleEditCoverLetter(letter: CoverLetterResult) {
    setEditingItem({ kind: 'cover-letter', item: letter });
    setEditValue(letter.content);
  }

  function handleSaveEdit() {
    if (!editingItem) return;
    if (editingItem.kind === 'resume') {
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

  const editorPending =
    updateResumeMutation.isPending || updateCoverLetterMutation.isPending;
  const editorTitle =
    editingItem?.kind === 'resume' ? 'Edit Resume Label' : 'Edit Cover Letter';
  const editorDescription =
    editingItem?.kind === 'resume'
      ? 'Rename how this resume version appears in the vault.'
      : 'Update the saved cover letter text.';

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-text-primary">Document Vault</h1>

      <Tabs tabs={TABS} activeTab={activeTab} onChange={setActiveTab} />

      {/* Resumes Tab */}
      {activeTab === 'resumes' && (
        <div className="space-y-4">
          {/* Upload Zone */}
          <Card padding="none">
            <div
              {...getRootProps()}
              className={`flex flex-col items-center justify-center p-8 border-2 border-dashed rounded-[var(--radius-lg)] cursor-pointer transition-colors ${
                isDragActive
                  ? 'border-accent-primary bg-accent-primary/5'
                  : 'border-border hover:border-border-focus'
              }`}
            >
              <input {...getInputProps()} />
              <UploadSimple size={32} weight="bold" className="text-text-muted mb-3" />
              <p className="text-sm text-text-primary font-medium">
                {isDragActive
                  ? 'Drop your resume here'
                  : 'Drag & drop a resume, or click to browse'}
              </p>
              <p className="text-xs text-text-muted mt-1">PDF or DOCX, max 10MB</p>
              {uploadMutation.isPending && (
                <p className="text-xs text-accent-primary mt-2">Uploading...</p>
              )}
            </div>
          </Card>

          {/* Resume Grid */}
          {resumesLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {Array.from({ length: 3 }).map((_, i) => (
                <SkeletonCard key={i} />
              ))}
            </div>
          ) : !resumes || resumes.length === 0 ? (
            <EmptyState
              icon={<FileText size={40} weight="bold" />}
              title="No resumes yet"
              description="Upload your first resume to start building your document vault"
            />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
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
      )}

      {/* Cover Letters Tab */}
      {activeTab === 'cover-letters' && (
        <div>
          {lettersLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {Array.from({ length: 3 }).map((_, i) => (
                <SkeletonCard key={i} />
              ))}
            </div>
          ) : !coverLetters || coverLetters.length === 0 ? (
            <EmptyState
              icon={<Scroll size={40} weight="bold" />}
              title="No cover letters yet"
              description="Generate cover letters from the Copilot page and they will appear here"
            />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {coverLetters.map((letter: CoverLetterResult) => (
                <CoverLetterCard
                  key={letter.id}
                  letter={letter}
                  onEdit={() => handleEditCoverLetter(letter)}
                  onDelete={() => deleteCoverLetterMutation.mutate(letter.id)}
                />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Resume Preview Modal */}
      <Modal
        open={!!previewResume}
        onClose={() => setPreviewResume(null)}
        title={previewResume?.filename ?? "Resume Preview"}
        size="lg"
      >
        {previewResume?.parsed_text ? (
          <pre className="text-sm text-text-primary whitespace-pre-wrap font-mono">
            {previewResume.parsed_text}
          </pre>
        ) : (
          <div className="flex items-center gap-3 text-text-muted py-8 justify-center">
            <FileText size={20} weight="bold" />
            <span className="text-sm">No text has been extracted from this resume yet.</span>
          </div>
        )}
      </Modal>

      <Modal
        open={!!editingItem}
        onClose={closeEditor}
        title={editorTitle}
        size="lg"
      >
        <div className="space-y-4">
          <p className="text-sm text-text-secondary">{editorDescription}</p>
          {editingItem?.kind === 'resume' ? (
            <Input
              label="Label"
              aria-label="Resume label"
              value={editValue}
              onChange={(e) => setEditValue(e.target.value)}
              placeholder="Optional label"
            />
          ) : (
            <Textarea
              label="Content"
              aria-label="Cover letter content"
              value={editValue}
              onChange={(e) => setEditValue(e.target.value)}
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
