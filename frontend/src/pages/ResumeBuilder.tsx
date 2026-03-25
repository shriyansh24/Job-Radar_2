import {
  Clock,
  Eye,
  FileText,
  Sparkle,
  Star,
  Trash,
  UploadSimple,
  UsersThree,
} from "@phosphor-icons/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { format } from "date-fns";
import { useCallback, useMemo, useState } from "react";
import { useDropzone } from "react-dropzone";
import { jobsApi, type Job } from "../api/jobs";
import { resumeApi, type ResumeTailorResponse, type ResumeVersion } from "../api/resume";
import { MetricStrip } from "../components/system/MetricStrip";
import { PageHeader } from "../components/system/PageHeader";
import { SectionHeader } from "../components/system/SectionHeader";
import { SplitWorkspace } from "../components/system/SplitWorkspace";
import { StateBlock } from "../components/system/StateBlock";
import { Surface } from "../components/system/Surface";
import Badge from "../components/ui/Badge";
import Button from "../components/ui/Button";
import EmptyState from "../components/ui/EmptyState";
import Modal from "../components/ui/Modal";
import { SkeletonCard } from "../components/ui/Skeleton";
import Select from "../components/ui/Select";
import Tabs from "../components/ui/Tabs";
import { toast } from "../components/ui/toastService";

const tabs = [
  { id: "upload", label: "Upload", icon: <UploadSimple size={14} weight="bold" /> },
  { id: "versions", label: "Versions", icon: <FileText size={14} weight="bold" /> },
  { id: "tailor", label: "Tailor", icon: <Sparkle size={14} weight="fill" /> },
  { id: "council", label: "AI Council", icon: <UsersThree size={14} weight="bold" /> },
] as const;

function VersionCard({
  version,
  onPreview,
}: {
  version: ResumeVersion;
  onPreview: () => void;
}) {
  return (
    <Surface
      tone="default"
      padding="lg"
      radius="xl"
      interactive
      onClick={onPreview}
      className="space-y-4"
    >
      <div className="flex items-start gap-3">
        <div className="flex size-12 shrink-0 items-center justify-center border-2 border-border bg-[var(--color-bg-tertiary)] shadow-[var(--shadow-xs)]">
          <FileText size={22} weight="bold" />
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <p className="truncate text-sm font-semibold text-text-primary">
              {version.filename ?? "Untitled resume"}
            </p>
            {version.is_default ? <Badge variant="success">Default</Badge> : null}
          </div>
          <p className="mt-2 flex items-center gap-1 text-xs text-text-muted">
            <Clock size={12} weight="bold" />
            {format(new Date(version.created_at), "PP")}
          </p>
        </div>
      </div>

      <div className="border-t-2 border-border pt-4">
        <div className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
          Parsed preview
        </div>
        <p className="mt-2 line-clamp-4 text-sm leading-6 text-text-secondary">
          {version.parsed_text || "No parsed text available yet."}
        </p>
      </div>
    </Surface>
  );
}

function TailorResultPanel({ result }: { result: ResumeTailorResponse }) {
  return (
    <Surface tone="default" padding="lg" radius="xl">
      <SectionHeader
        title="Tailored resume"
        description="Preview the scoring delta, rewritten content, and the requirement gaps identified by the backend tailoring pipeline."
      />

      <div className="mt-5 grid gap-4 lg:grid-cols-2">
        <div className="border-2 border-border bg-[var(--color-bg-tertiary)] p-5 shadow-[var(--shadow-xs)]">
          <div className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
            Tailoring summary
          </div>
          <p className="mt-3 text-sm leading-6 text-text-secondary">
            {result.summary || "No summary returned."}
          </p>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="border-2 border-border bg-card p-4 shadow-[var(--shadow-xs)]">
            <div className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
              ATS score before
            </div>
            <div className="mt-3 text-3xl font-black uppercase tracking-[-0.05em] text-text-primary">
              {result.ats_score_before}
            </div>
          </div>
          <div className="border-2 border-border bg-accent-primary/8 p-4 shadow-[var(--shadow-xs)]">
            <div className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
              ATS score after
            </div>
            <div className="mt-3 text-3xl font-black uppercase tracking-[-0.05em] text-accent-primary">
              {result.ats_score_after}
            </div>
          </div>
        </div>
      </div>

      {result.enhanced_bullets.length ? (
        <div className="mt-5 space-y-2">
          <div className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
            Enhanced bullets
          </div>
          <div className="space-y-2">
            {result.enhanced_bullets.map((bullet, index) => (
              <div
                key={`${bullet.original}-${index}`}
                className="border-2 border-border bg-[var(--color-bg-tertiary)] px-4 py-3 text-sm text-text-secondary"
              >
                <div className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
                  Original
                </div>
                <div className="mt-2">{bullet.original}</div>
                <div className="mt-4 font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
                  Enhanced
                </div>
                <div className="mt-2 text-text-primary">{bullet.enhanced}</div>
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {result.reordered_experience.length ? (
        <div className="mt-5 space-y-2">
          <div className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
            Reordered experience
          </div>
          <div className="grid gap-3 lg:grid-cols-2">
            {result.reordered_experience.map((entry) => (
              <div key={entry.company} className="border-2 border-border bg-card p-4 shadow-[var(--shadow-xs)]">
                <div className="text-sm font-semibold uppercase tracking-[-0.03em] text-text-primary">
                  {entry.company}
                </div>
                <ul className="mt-3 space-y-2 text-sm leading-6 text-text-secondary">
                  {entry.bullets.map((bullet, index) => (
                    <li key={`${entry.company}-${index}`}>{bullet}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {result.skills_section.length ? (
        <div className="mt-5 space-y-2">
          <div className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
            Skills section
          </div>
          <div className="flex flex-wrap gap-2">
            {result.skills_section.map((skill) => (
              <Badge key={skill} variant="info">
                {skill}
              </Badge>
            ))}
          </div>
        </div>
      ) : null}
    </Surface>
  );
}

export default function ResumeBuilder() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState("upload");
  const [selectedResume, setSelectedResume] = useState("");
  const [selectedJob, setSelectedJob] = useState("");
  const [showPreview, setShowPreview] = useState<ResumeVersion | null>(null);

  const { data: versions, isLoading } = useQuery({
    queryKey: ["resume-versions"],
    queryFn: () => resumeApi.listVersions().then((response) => response.data),
  });

  const { data: jobs } = useQuery({
    queryKey: ["jobs", "all"],
    queryFn: () => jobsApi.list({ page_size: 100 }).then((response) => response.data),
  });

  const uploadMutation = useMutation({
    mutationFn: (file: File) => resumeApi.upload(file),
    onSuccess: () => {
      toast("success", "Resume uploaded");
      queryClient.invalidateQueries({ queryKey: ["resume-versions"] });
    },
    onError: () => toast("error", "Upload failed"),
  });

  const tailorMutation = useMutation({
    mutationFn: () => resumeApi.tailor(selectedResume, selectedJob),
    onSuccess: () => toast("success", "Resume tailored"),
    onError: () => toast("error", "Tailoring failed"),
  });

  const councilMutation = useMutation({
    mutationFn: () => resumeApi.council(selectedResume),
    onSuccess: () => toast("success", "Council evaluation complete"),
    onError: () => toast("error", "Evaluation failed"),
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

  const jobOptions = (jobs?.items || []).map((job: Job) => ({
    value: job.id,
    label: `${job.title} - ${job.company_name || "Unknown"}`,
  }));

  const resumeOptions = (versions || []).map((version: ResumeVersion) => ({
    value: version.id,
    label: version.filename ?? "Untitled resume",
  }));

  const tailorResult = tailorMutation.data?.data ?? null;

  const metrics = useMemo(
    () => [
      {
        key: "versions",
        label: "Versions",
        value: (versions?.length ?? 0).toLocaleString(),
        hint: "Uploaded resume versions currently available for reuse.",
        icon: <FileText size={18} weight="bold" />,
      },
      {
        key: "defaults",
        label: "Default set",
        value: `${versions?.filter((version) => version.is_default).length ?? 0}`,
        hint: "Versions marked as the current default baseline.",
        icon: <Star size={18} weight="fill" />,
        tone: "success" as const,
      },
      {
        key: "jobs",
        label: "Jobs loaded",
        value: `${jobs?.items.length ?? 0}`,
        hint: "Target roles available to ground tailoring prompts.",
        icon: <Sparkle size={18} weight="bold" />,
      },
      {
        key: "selection",
        label: "Selection",
        value: selectedResume ? "Ready" : "None",
        hint: "Whether a resume is selected for tailoring or council review.",
        icon: <UsersThree size={18} weight="bold" />,
      },
    ],
    [jobs?.items.length, selectedResume, versions]
  );

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Prepare"
        title="Resume Builder"
        description="Upload resumes, manage versions, tailor a draft to a job, and run the AI council without leaving the workspace."
      />

      <MetricStrip items={metrics} />

      <Tabs tabs={tabs.map((tab) => ({ ...tab }))} activeTab={activeTab} onChange={setActiveTab} />

      {activeTab === "upload" ? (
        <SplitWorkspace
          primary={
            <Surface tone="default" padding="lg" radius="xl">
              <SectionHeader
                title="Upload runway"
                description="Feed the workspace a strong base resume first. That source version becomes the anchor for tailoring and review."
              />
              <button
                type="button"
                {...getRootProps()}
                className="mt-5 flex w-full flex-col items-center justify-center border-2 border-dashed border-border bg-[var(--color-bg-tertiary)] px-6 py-14 text-center transition-colors hover:bg-card"
              >
                <input {...getInputProps()} />
                <UploadSimple size={40} weight="bold" className="text-text-primary" />
                <p className="mt-5 text-xl font-black uppercase tracking-[-0.05em] text-text-primary">
                  {isDragActive ? "Drop your resume here" : "Drag & drop your resume here"}
                </p>
                <p className="mt-3 text-sm leading-6 text-muted-foreground">or click to browse</p>
                <p className="mt-2 font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
                  Supports PDF, DOCX, TXT
                </p>
                {uploadMutation.isPending ? (
                  <p className="mt-4 text-sm font-semibold text-accent-primary">Uploading...</p>
                ) : null}
                {uploadMutation.isSuccess ? (
                  <p className="mt-4 text-sm font-semibold text-accent-secondary">Upload complete!</p>
                ) : null}
              </button>
            </Surface>
          }
          secondary={
            <div className="space-y-4">
              <StateBlock
                tone="success"
                icon={<UploadSimple size={18} weight="bold" />}
                title="Base material"
                description="Keep one clean, current resume in the system before generating tailored variants."
              />
              <StateBlock
                tone="neutral"
                icon={<FileText size={18} weight="bold" />}
                title="Version count"
                description={`${versions?.length ?? 0} resume versions currently available in the workspace.`}
              />
            </div>
          }
        />
      ) : null}

      {activeTab === "versions" ? (
        <SplitWorkspace
          primary={
            isLoading ? (
              <div className="grid gap-4 md:grid-cols-2">
                {Array.from({ length: 4 }).map((_, index) => (
                  <SkeletonCard key={index} />
                ))}
              </div>
            ) : !versions || versions.length === 0 ? (
              <Surface tone="default" padding="lg" radius="xl">
                <EmptyState
                  icon={<FileText size={40} weight="bold" />}
                  title="No resumes yet"
                  description="Upload a resume to get started with tailoring and evaluation"
                />
              </Surface>
            ) : (
              <div className="grid gap-4 md:grid-cols-2">
                {versions.map((version: ResumeVersion) => (
                  <VersionCard
                    key={version.id}
                    version={version}
                    onPreview={() => setShowPreview(version)}
                  />
                ))}
              </div>
            )
          }
          secondary={
            <div className="space-y-4">
              <StateBlock
                tone="neutral"
                icon={<Eye size={18} weight="bold" />}
                title="Preview behavior"
                description="Selecting a version opens the parsed text so you can quickly sanity-check what the system extracted."
              />
            </div>
          }
        />
      ) : null}

      {activeTab === "tailor" ? (
        <SplitWorkspace
          primary={
            <div className="space-y-6">
              <Surface tone="default" padding="lg" radius="xl">
                <SectionHeader
                  title="Tailor a draft"
                  description="Select a resume and a job to generate a tailored version optimized for the position."
                />
                <div className="mt-5 grid gap-4 md:grid-cols-2">
                  <Select
                    label="Resume Version"
                    options={resumeOptions}
                    value={selectedResume}
                    onChange={(event) => setSelectedResume(event.target.value)}
                    placeholder="Select a resume..."
                  />
                  <Select
                    label="Target Job"
                    options={jobOptions}
                    value={selectedJob}
                    onChange={(event) => setSelectedJob(event.target.value)}
                    placeholder="Select a job..."
                  />
                </div>
                <div className="mt-5">
                  <Button
                    variant="primary"
                    loading={tailorMutation.isPending}
                    disabled={!selectedResume || !selectedJob}
                    onClick={() => tailorMutation.mutate()}
                    icon={<Sparkle size={14} weight="fill" />}
                  >
                    Tailor Resume
                  </Button>
                </div>
              </Surface>

              {tailorResult ? <TailorResultPanel result={tailorResult} /> : null}
            </div>
          }
          secondary={
            <div className="space-y-4">
              {tailorResult?.stage2_output?.missing_requirements.length ? (
                <StateBlock
                  tone="warning"
                  icon={<Sparkle size={18} weight="bold" />}
                  title="Missing requirements"
                  description={tailorResult.stage2_output.missing_requirements.join(", ")}
                />
              ) : (
                <StateBlock
                  tone="muted"
                  icon={<Sparkle size={18} weight="bold" />}
                  title="Awaiting a run"
                  description="Choose a resume and a target job to generate the first tailored draft."
                />
              )}
              {tailorResult?.stage2_output?.transferable_skills.length ? (
                <StateBlock
                  tone="success"
                  icon={<UsersThree size={18} weight="bold" />}
                  title="Transferable skills"
                  description={tailorResult.stage2_output.transferable_skills.join(", ")}
                />
              ) : null}
            </div>
          }
        />
      ) : null}

      {activeTab === "council" ? (
        <SplitWorkspace
          primary={
            <Surface tone="default" padding="lg" radius="xl">
              <SectionHeader
                title="AI Council"
                description="Get your resume evaluated by multiple AI models for comprehensive feedback."
              />
              <div className="mt-5 space-y-4">
                <Select
                  label="Resume Version"
                  options={resumeOptions}
                  value={selectedResume}
                  onChange={(event) => setSelectedResume(event.target.value)}
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
              </div>

              {councilMutation.data ? (
                <div className="mt-6 space-y-4">
                  <div className="border-2 border-border bg-[var(--color-bg-tertiary)] p-5 text-center">
                    <div className="mono-num text-5xl font-bold text-text-primary">
                      {(councilMutation.data.data.overall_score ?? 0).toFixed(1)}
                    </div>
                    <p className="mt-2 text-sm text-muted-foreground">Average Score</p>
                  </div>
                  {councilMutation.data.data.evaluations.map((evaluation) => (
                    <Surface key={evaluation.model} tone="subtle" padding="md" radius="xl">
                      <div className="flex items-center justify-between gap-3">
                        <span className="text-sm font-semibold text-text-primary">{evaluation.model}</span>
                        <Badge
                          variant={evaluation.score >= 8 ? "success" : evaluation.score >= 5 ? "warning" : "danger"}
                        >
                          {evaluation.score}/10
                        </Badge>
                      </div>
                      <p className="mt-3 text-sm leading-6 text-text-secondary">{evaluation.feedback}</p>
                    </Surface>
                  ))}
                </div>
              ) : null}
            </Surface>
          }
          secondary={
            <div className="space-y-4">
              <StateBlock
                tone="neutral"
                icon={<UsersThree size={18} weight="bold" />}
                title="Council mode"
                description="Use this after the resume is structurally solid. It is best for quality scoring and blind-spot detection."
              />
            </div>
          }
        />
      ) : null}

      <Modal
        open={!!showPreview}
        onClose={() => setShowPreview(null)}
        title={showPreview?.filename ?? "Resume Preview"}
        size="lg"
      >
        {showPreview?.parsed_text ? (
          <pre className="whitespace-pre-wrap font-mono text-sm text-text-primary">
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
