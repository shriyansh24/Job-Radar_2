import {
  Clock,
  FileText,
  Sparkle,
  Star,
  Trash,
  UploadSimple,
  UsersThree,
} from "@phosphor-icons/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { format } from "date-fns";
import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { jobsApi, type Job } from "../api/jobs";
import { resumeApi, type ResumeVersion } from "../api/resume";
import Badge from "../components/ui/Badge";
import Button from "../components/ui/Button";
import Card from "../components/ui/Card";
import EmptyState from "../components/ui/EmptyState";
import Modal from "../components/ui/Modal";
import { SkeletonCard } from "../components/ui/Skeleton";
import Select from "../components/ui/Select";
import Tabs from "../components/ui/Tabs";
import { PageHeader } from "../components/system/PageHeader";
import { toast } from "../components/ui/toastService";

const tabs = [
  { id: "upload", label: "Upload", icon: <UploadSimple size={14} weight="bold" /> },
  { id: "versions", label: "Versions", icon: <FileText size={14} weight="bold" /> },
  { id: "tailor", label: "Tailor", icon: <Sparkle size={14} weight="fill" /> },
  { id: "council", label: "AI Council", icon: <UsersThree size={14} weight="bold" /> },
];

export default function ResumeBuilder() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState('upload');
  const [selectedResume, setSelectedResume] = useState<string>('');
  const [selectedJob, setSelectedJob] = useState<string>('');
  const [showPreview, setShowPreview] = useState<ResumeVersion | null>(null);

  const { data: versions, isLoading } = useQuery({
    queryKey: ['resume-versions'],
    queryFn: () => resumeApi.listVersions().then((r) => r.data),
  });

  const { data: jobs } = useQuery({
    queryKey: ['jobs', 'all'],
    queryFn: () => jobsApi.list({ page_size: 100 }).then((r) => r.data),
  });

  const uploadMutation = useMutation({
    mutationFn: (file: File) => resumeApi.upload(file),
    onSuccess: () => {
      toast('success', 'Resume uploaded');
      queryClient.invalidateQueries({ queryKey: ['resume-versions'] });
    },
    onError: () => toast('error', 'Upload failed'),
  });

  const tailorMutation = useMutation({
    mutationFn: () => resumeApi.tailor(selectedResume, selectedJob),
    onSuccess: () => toast('success', 'Resume tailored (preview ready)'),
    onError: () => toast('error', 'Tailoring failed'),
  });

  const councilMutation = useMutation({
    mutationFn: () => resumeApi.council(selectedResume),
    onSuccess: () => toast('success', 'Council evaluation complete'),
    onError: () => toast('error', 'Evaluation failed'),
  });

  const onDrop = useCallback((accepted: File[]) => {
    const file = accepted[0];
    if (file) uploadMutation.mutate(file);
  }, [uploadMutation]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'], 'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'] },
    maxFiles: 1,
  });

  const jobOptions = (jobs?.items || []).map((j: Job) => ({
    value: j.id,
    label: `${j.title} - ${j.company_name || 'Unknown'}`,
  }));

  const resumeOptions = (versions || []).map((v: ResumeVersion) => ({
    value: v.id,
    label: v.filename ?? 'Untitled resume',
  }));

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Prepare"
        title="Resume Builder"
        description="Upload resumes, manage versions, tailor a draft to a job, and run the AI council without leaving the workspace."
      />

      <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

      {activeTab === 'upload' && (
        <Card padding="none">
          <div
            {...getRootProps()}
            className={`flex flex-col items-center justify-center p-12 border-2 border-dashed rounded-[var(--radius-lg)] cursor-pointer transition-colors ${
              isDragActive ? 'border-accent-primary bg-accent-primary/5' : 'border-border hover:border-border-focus'
            }`}
          >
            <input {...getInputProps()} />
            <UploadSimple size={40} weight="bold" className="text-text-muted mb-4" />
            <p className="text-base text-text-primary font-medium">
              {isDragActive ? 'Drop your resume here' : 'Drag & drop your resume here'}
            </p>
            <p className="text-sm text-text-secondary mt-1">or click to browse</p>
            <p className="text-xs text-text-muted mt-3">Supports PDF, DOCX, TXT</p>
            {uploadMutation.isPending && (
              <p className="text-sm text-accent-primary mt-3 animate-pulse">Uploading...</p>
            )}
            {uploadMutation.isSuccess && (
              <p className="text-sm text-accent-success mt-3">Upload complete!</p>
            )}
          </div>
        </Card>
      )}

      {activeTab === 'versions' && (
        <div className="space-y-4">
          {/* Resume Versions List */}
          {isLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Array.from({ length: 3 }).map((_, i) => <SkeletonCard key={i} />)}
            </div>
          ) : !versions || versions.length === 0 ? (
            <EmptyState
              icon={<FileText size={40} weight="bold" />}
              title="No resumes yet"
              description="Upload a resume to get started with tailoring and evaluation"
            />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {versions.map((v: ResumeVersion) => (
                <Card key={v.id} hover onClick={() => setShowPreview(v)}>
                  <div className="flex items-start gap-3">
                    <FileText size={24} weight="bold" className="text-accent-primary shrink-0 mt-0.5" />
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <p className="text-sm font-medium text-text-primary truncate">
                          {v.filename ?? 'Untitled resume'}
                        </p>
                        {v.is_default && (
                          <Badge variant="success" size="sm">
                            <Star size={10} weight="fill" className="mr-0.5" />
                            Default
                          </Badge>
                        )}
                      </div>
                      <p className="text-xs text-text-muted flex items-center gap-1 mt-1">
                        <Clock size={10} weight="bold" />
                        {format(new Date(v.created_at), 'PP')}
                      </p>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === 'tailor' && (
        <Card>
          <div className="space-y-4">
            <p className="text-sm text-text-secondary">
              Select a resume and a job to generate a tailored version optimized for the position.
            </p>
            <Select
              label="Resume Version"
              options={resumeOptions}
              value={selectedResume}
              onChange={(e) => setSelectedResume(e.target.value)}
              placeholder="Select a resume..."
            />
            <Select
              label="Target Job"
              options={jobOptions}
              value={selectedJob}
              onChange={(e) => setSelectedJob(e.target.value)}
              placeholder="Select a job..."
            />
            <Button
              variant="primary"
              loading={tailorMutation.isPending}
              disabled={!selectedResume || !selectedJob}
              onClick={() => tailorMutation.mutate()}
              icon={<Sparkle size={14} weight="fill" />}
            >
              Tailor Resume
            </Button>

            {tailorMutation.data && (
              <div className="mt-4 space-y-4">
                <Card>
                  <h3 className="text-sm font-medium text-text-secondary mb-2">Tailored Resume</h3>
                  <pre className="text-xs text-text-primary whitespace-pre-wrap font-mono max-h-80 overflow-auto">
                    {tailorMutation.data.data.tailored_text}
                  </pre>
                </Card>
                {tailorMutation.data.data.suggestions.length > 0 && (
                  <Card>
                    <h3 className="text-sm font-medium text-text-secondary mb-2">Suggestions</h3>
                    <ul className="space-y-1.5">
                      {tailorMutation.data.data.suggestions.map((s: string, i: number) => (
                        <li key={i} className="text-sm text-text-primary flex items-start gap-2">
                          <span className="text-accent-primary mt-0.5 shrink-0">&#8226;</span>
                          {s}
                        </li>
                      ))}
                    </ul>
                  </Card>
                )}
                {tailorMutation.data.data.sections_modified.length > 0 && (
                  <div className="flex flex-wrap gap-1.5">
                    <span className="text-xs text-text-muted">Sections modified:</span>
                    {tailorMutation.data.data.sections_modified.map((s: string) => (
                      <Badge key={s} variant="info" size="sm">{s}</Badge>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </Card>
      )}

      {activeTab === 'council' && (
        <Card>
          <div className="space-y-4">
            <p className="text-sm text-text-secondary">
              Get your resume evaluated by multiple AI models for comprehensive feedback.
            </p>
            <Select
              label="Resume Version"
              options={resumeOptions}
              value={selectedResume}
              onChange={(e) => setSelectedResume(e.target.value)}
              placeholder="Select a resume..."
            />
            <Button
              variant="primary"
              loading={councilMutation.isPending}
              disabled={!selectedResume}
              onClick={() => councilMutation.mutate()}
              icon={<UsersThree size={14} weight="bold" />}
            >
              Get AI Evaluation
            </Button>

            {councilMutation.data && (
              <div className="mt-4 space-y-3">
                <div className="text-center">
                  <p className="text-3xl font-bold text-accent-primary">
                    {(councilMutation.data.data.overall_score ?? 0).toFixed(1)}
                  </p>
                  <p className="text-sm text-text-muted">Average Score</p>
                </div>
                {councilMutation.data.data.evaluations.map((s: { model: string; score: number; feedback: string }) => (
                  <Card key={s.model} padding="sm">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-text-primary">{s.model}</span>
                      <Badge variant={s.score >= 8 ? 'success' : s.score >= 5 ? 'warning' : 'danger'}>
                        {s.score}/10
                      </Badge>
                    </div>
                    <p className="text-xs text-text-secondary">{s.feedback}</p>
                  </Card>
                ))}
              </div>
            )}
          </div>
        </Card>
      )}

      {/* Preview Modal */}
      <Modal
        open={!!showPreview}
        onClose={() => setShowPreview(null)}
        title={showPreview?.filename ?? "Resume Preview"}
        size="lg"
      >
        {showPreview?.parsed_text ? (
          <pre className="text-sm text-text-primary whitespace-pre-wrap font-mono">
            {showPreview.parsed_text}
          </pre>
        ) : (
          <div className="flex items-center gap-3 text-text-muted">
            <Trash size={16} weight="bold" />
            <span className="text-sm">No text extracted from this resume yet.</span>
          </div>
        )}
      </Modal>
    </div>
  );
}
