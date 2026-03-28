import { FileText, Sparkle, Star, UploadSimple, UsersThree } from "@phosphor-icons/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useDropzone } from "react-dropzone";
import { jobsApi, type Job } from "../api/jobs";
import { resumeApi, type ResumeVersion } from "../api/resume";
import { ResumeBuilderCouncilWorkspace } from "../components/resume-builder/ResumeBuilderCouncilWorkspace";
import { ResumeBuilderPreviewModal } from "../components/resume-builder/ResumeBuilderPreviewModal";
import { ResumeBuilderTailorWorkspace } from "../components/resume-builder/ResumeBuilderTailorWorkspace";
import { ResumeBuilderUploadWorkspace } from "../components/resume-builder/ResumeBuilderUploadWorkspace";
import { ResumeBuilderVersionsWorkspace } from "../components/resume-builder/ResumeBuilderVersionsWorkspace";
import { MetricStrip } from "../components/system/MetricStrip";
import { PageHeader } from "../components/system/PageHeader";
import Tabs from "../components/ui/Tabs";
import { toast } from "../components/ui/toastService";

const tabs = [
  { id: "upload", label: "Upload", icon: <UploadSimple size={14} weight="bold" /> },
  { id: "versions", label: "Versions", icon: <FileText size={14} weight="bold" /> },
  { id: "tailor", label: "Tailor", icon: <Sparkle size={14} weight="fill" /> },
  { id: "council", label: "Council", icon: <UsersThree size={14} weight="bold" /> },
] as const;

type SelectOption = {
  value: string;
  label: string;
};

export default function ResumeBuilder() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState("upload");
  const [selectedResume, setSelectedResume] = useState("");
  const [selectedJob, setSelectedJob] = useState("");
  const [showPreview, setShowPreview] = useState<ResumeVersion | null>(null);
  const [selectedTemplateId, setSelectedTemplateId] = useState("");

  const { data: versions, isLoading } = useQuery({
    queryKey: ["resume-versions"],
    queryFn: () => resumeApi.listVersions().then((response) => response.data),
  });

  const { data: templates = [] } = useQuery({
    queryKey: ["resume-templates"],
    queryFn: () => resumeApi.listTemplates().then((response) => response.data),
  });

  const { data: previewData, isLoading: previewLoading } = useQuery({
    queryKey: ["resume-preview", showPreview?.id, selectedTemplateId],
    queryFn: () =>
      resumeApi.preview(showPreview!.id, selectedTemplateId).then((response) => response.data),
    enabled: !!showPreview && !!selectedTemplateId,
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
    mutationFn: () => resumeApi.council(selectedResume, selectedJob || undefined),
    onSuccess: () => toast("success", "Council review complete"),
    onError: () => toast("error", "Evaluation failed"),
  });

  const exportMutation = useMutation({
    mutationFn: () => {
      if (!showPreview || !selectedTemplateId) {
        throw new Error("Preview selection missing");
      }
      return resumeApi.exportVersion(showPreview.id, selectedTemplateId);
    },
    onSuccess: (response) => {
      const blobUrl = URL.createObjectURL(response.data);
      const link = document.createElement("a");
      const contentDisposition = response.headers["content-disposition"] ?? "";
      const filenameMatch = /filename="([^"]+)"/.exec(contentDisposition);
      link.href = blobUrl;
      link.download = filenameMatch?.[1] ?? `${showPreview?.filename ?? "resume"}.pdf`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(blobUrl);
      toast("success", "Resume export ready");
    },
    onError: () => toast("error", "PDF export unavailable"),
  });

  useEffect(() => {
    if (!templates.length) {
      return;
    }
    setSelectedTemplateId((current) =>
      templates.some((template) => template.id === current) ? current : templates[0].id
    );
  }, [templates]);

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

  const jobOptions: SelectOption[] = (jobs?.items || []).map((job: Job) => ({
    value: job.id,
    label: `${job.title} - ${job.company_name || "Unknown"}`,
  }));

  const resumeOptions: SelectOption[] = (versions || []).map((version: ResumeVersion) => ({
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
        <ResumeBuilderUploadWorkspace
          rootProps={getRootProps()}
          inputProps={getInputProps()}
          isDragActive={isDragActive}
          uploadPending={uploadMutation.isPending}
          uploadSuccess={uploadMutation.isSuccess}
          versionCount={versions?.length ?? 0}
          selectedResume={selectedResume}
        />
      ) : null}

      {activeTab === "versions" ? (
        <ResumeBuilderVersionsWorkspace
          isLoading={isLoading}
          versions={versions}
          onPreview={setShowPreview}
        />
      ) : null}

      {activeTab === "tailor" ? (
        <ResumeBuilderTailorWorkspace
          resumeOptions={resumeOptions}
          jobOptions={jobOptions}
          selectedResume={selectedResume}
          selectedJob={selectedJob}
          onResumeChange={setSelectedResume}
          onJobChange={setSelectedJob}
          tailorPending={tailorMutation.isPending}
          onTailor={() => tailorMutation.mutate()}
          tailorResult={tailorResult}
        />
      ) : null}

      {activeTab === "council" ? (
        <ResumeBuilderCouncilWorkspace
          resumeOptions={resumeOptions}
          jobOptions={jobOptions}
          selectedResume={selectedResume}
          selectedJob={selectedJob}
          onResumeChange={setSelectedResume}
          onJobChange={setSelectedJob}
          councilPending={councilMutation.isPending}
          onRunCouncil={() => councilMutation.mutate()}
          councilResult={councilMutation.data?.data ?? null}
        />
      ) : null}

      <ResumeBuilderPreviewModal
        showPreview={showPreview}
        templates={templates}
        selectedTemplateId={selectedTemplateId}
        onTemplateChange={setSelectedTemplateId}
        previewData={previewData}
        previewLoading={previewLoading}
        exportLoading={exportMutation.isPending}
        onClose={() => setShowPreview(null)}
        onExport={() => exportMutation.mutate()}
      />
    </div>
  );
}
