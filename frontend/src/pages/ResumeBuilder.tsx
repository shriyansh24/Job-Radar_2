import {
  FileText,
  Sparkle,
  Star,
  UploadSimple,
  UsersThree,
  Eye,
} from "@phosphor-icons/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useCallback, useMemo, useState } from "react";
import { useDropzone } from "react-dropzone";
import { jobsApi, type Job } from "../api/jobs";
import { resumeApi, type ResumeVersion } from "../api/resume";
import { MetricStrip } from "../components/system/MetricStrip";
import { PageHeader } from "../components/system/PageHeader";
import { SectionHeader } from "../components/system/SectionHeader";
import { SplitWorkspace } from "../components/system/SplitWorkspace";
import { StateBlock } from "../components/system/StateBlock";
import { Surface } from "../components/system/Surface";
import Button from "../components/ui/Button";
import EmptyState from "../components/ui/EmptyState";
import Modal from "../components/ui/Modal";
import { SkeletonCard } from "../components/ui/Skeleton";
import Select from "../components/ui/Select";
import Tabs from "../components/ui/Tabs";
import { toast } from "../components/ui/toastService";
import {
  ResumeCouncilSummary,
  ResumeStatusRail,
  ResumeTailorResultPanel,
  ResumeVersionCard,
} from "../components/resume/ResumeWidgets";

const tabs = [
  { id: "upload", label: "Upload", icon: <UploadSimple size={14} weight="bold" /> },
  { id: "versions", label: "Versions", icon: <FileText size={14} weight="bold" /> },
  { id: "tailor", label: "Tailor", icon: <Sparkle size={14} weight="fill" /> },
  { id: "council", label: "Council", icon: <UsersThree size={14} weight="bold" /> },
] as const;

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
    onSuccess: () => toast("success", "Council review complete"),
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
      { key: "versions", label: "Versions", value: (versions?.length ?? 0).toLocaleString(), hint: "Loaded resumes.", icon: <FileText size={18} weight="bold" /> },
      {
        key: "defaults",
        label: "Default set",
        value: `${versions?.filter((version) => version.is_default).length ?? 0}`,
        hint: "Current baseline.",
        icon: <Star size={18} weight="fill" />,
        tone: "success" as const,
      },
      { key: "jobs", label: "Jobs", value: `${jobs?.items.length ?? 0}`, hint: "Target roles.", icon: <Sparkle size={18} weight="bold" /> },
      {
        key: "selection",
        label: "Selection",
        value: selectedResume ? "Ready" : "None",
        hint: "Resume selected.",
        icon: <UsersThree size={18} weight="bold" />,
      },
    ],
    [jobs?.items.length, selectedResume, versions]
  );

  return (
    <div className="space-y-6">
      <PageHeader
        className="hero-panel"
        eyebrow="Prepare"
        title="Resume Builder"
        description="Upload resumes, manage versions, tailor drafts, and review council scores."
      />

      <MetricStrip items={metrics} />

      <Tabs tabs={tabs.map((tab) => ({ ...tab }))} activeTab={activeTab} onChange={setActiveTab} />

      {activeTab === "upload" ? (
        <SplitWorkspace
          primary={
            <Surface tone="default" padding="lg" radius="xl">
              <SectionHeader title="Upload" description="Add a base resume before tailoring or review." />
              <button
                type="button"
                {...getRootProps()}
                className="hero-panel mt-5 flex w-full flex-col items-center justify-center border-2 border-dashed border-border px-6 py-14 text-center transition-colors"
              >
                <input {...getInputProps()} />
                <UploadSimple size={40} weight="bold" className="text-text-primary" />
                <p className="mt-5 text-xl font-black uppercase tracking-[-0.05em] text-text-primary">
                  {isDragActive ? "Drop the file here" : "Drag and drop a resume"}
                </p>
                <p className="mt-3 text-sm leading-6 text-muted-foreground">or click to browse</p>
                <p className="mt-2 font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
                  PDF and DOCX
                </p>
                {uploadMutation.isPending ? <p className="mt-4 text-sm font-semibold text-accent-primary">Uploading...</p> : null}
                {uploadMutation.isSuccess ? <p className="mt-4 text-sm font-semibold text-accent-secondary">Upload complete</p> : null}
              </button>
            </Surface>
          }
          secondary={
            <div className="space-y-4">
              <StateBlock
                tone="success"
                icon={<UploadSimple size={18} weight="bold" />}
                title="Source file"
                description="Keep one current resume in the workspace before tailoring or review."
              />
              <ResumeStatusRail versionCount={versions?.length ?? 0} selectedResume={selectedResume} />
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
                  title="No resumes"
                  description="Upload a resume to start tracking versions."
                />
              </Surface>
            ) : (
              <div className="grid gap-4 md:grid-cols-2">
                {versions.map((version) => (
                  <ResumeVersionCard key={version.id} version={version} onPreview={() => setShowPreview(version)} />
                ))}
              </div>
            )
          }
          secondary={
            <div className="space-y-4">
              <StateBlock
                tone="neutral"
                icon={<Eye size={18} weight="bold" />}
                title="Preview"
                description="Open a version to inspect parsed text."
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
                <SectionHeader title="Tailor" description="Select a resume and job to generate a draft." />
                <div className="mt-5 grid gap-4 md:grid-cols-2">
                  <Select
                    label="Resume version"
                    options={resumeOptions}
                    value={selectedResume}
                    onChange={(event) => setSelectedResume(event.target.value)}
                    placeholder="Select a resume..."
                  />
                  <Select
                    label="Target job"
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
                    Tailor
                  </Button>
                </div>
              </Surface>

              {tailorResult ? <ResumeTailorResultPanel result={tailorResult} /> : null}
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
                  title="Waiting"
                  description="Choose a resume and a job to generate the first draft."
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
              <SectionHeader title="Council" description="Run a multi-model review on the selected resume." />
              <div className="mt-5 space-y-4">
                <Select
                  label="Resume version"
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
                  Run council
                </Button>
              </div>

              {councilMutation.data ? (
                <ResumeCouncilSummary
                  score={councilMutation.data.data.overall_score ?? 0}
                  evaluations={councilMutation.data.data.evaluations}
                />
              ) : null}
            </Surface>
          }
          secondary={
            <div className="space-y-4">
              <StateBlock
                tone="neutral"
                icon={<UsersThree size={18} weight="bold" />}
                title="Review"
                description="Use council feedback to compare models and tune the draft."
              />
            </div>
          }
        />
      ) : null}

      <Modal
        open={!!showPreview}
        onClose={() => setShowPreview(null)}
        title={showPreview?.filename ?? "Resume preview"}
        size="lg"
      >
        {showPreview?.parsed_text ? (
          <pre className="whitespace-pre-wrap font-mono text-sm text-text-primary">{showPreview.parsed_text}</pre>
        ) : (
          <div className="flex items-center justify-center gap-3 py-8 text-text-muted">
            <FileText size={20} weight="bold" />
            <span className="text-sm">No parsed text available yet.</span>
          </div>
        )}
      </Modal>
    </div>
  );
}
