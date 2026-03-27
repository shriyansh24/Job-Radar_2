import { Sparkle } from "@phosphor-icons/react";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import {
  type InterviewPrepBundle,
  type InterviewPrepRequest,
} from "../../api/interview";
import { jobsApi, type Job } from "../../api/jobs";
import { SectionHeader } from "../system/SectionHeader";
import { Surface } from "../system/Surface";
import Button from "../ui/Button";
import Select from "../ui/Select";
import Textarea from "../ui/Textarea";
import { toast } from "../ui/toastService";
import { InterviewPrepBundlePanel } from "./InterviewPrepBundlePanel";

const STAGE_OPTIONS = [
  { value: "general", label: "General" },
  { value: "technical", label: "Technical" },
  { value: "behavioral", label: "Behavioral" },
  { value: "onsite", label: "Onsite" },
  { value: "manager", label: "Manager" },
] as const;

export function InterviewPreparePanel({
  bundle,
  isPending,
  onPrepare,
}: {
  bundle: InterviewPrepBundle | null;
  isPending: boolean;
  onPrepare: (params: InterviewPrepRequest) => void;
}) {
  const [selectedJob, setSelectedJob] = useState("");
  const [stage, setStage] = useState("general");
  const [resumeText, setResumeText] = useState("");

  const { data: jobs } = useQuery({
    queryKey: ["jobs", "all"],
    queryFn: () => jobsApi.list({ page_size: 100 }).then((response) => response.data),
  });

  const jobOptions = (jobs?.items || []).map((job: Job) => ({
    value: job.id,
    label: `${job.title} - ${job.company_name || "Unknown"}`,
  }));

  const handleSubmit = () => {
    if (!selectedJob) {
      toast("warning", "Select a job first");
      return;
    }

    if (resumeText.trim().length < 50) {
      toast("warning", "Resume text needs at least 50 characters");
      return;
    }

    onPrepare({
      job_id: selectedJob,
      resume_text: resumeText.trim(),
      stage,
    });
  };

  return (
    <div className="space-y-6">
      <Surface tone="default" padding="lg" radius="xl" className="hero-panel">
        <SectionHeader
          title="Prepare interview bundle"
          description="Pick a job, paste resume text, and generate a full prep pack."
        />
        <div className="mt-5 space-y-4">
          <div className="grid gap-4 lg:grid-cols-2">
            <Select
              label="Target job"
              options={jobOptions}
              value={selectedJob}
              onChange={(event) => setSelectedJob(event.target.value)}
              placeholder="Select a job..."
            />
            <Select
              label="Interview stage"
              options={STAGE_OPTIONS.map((option) => ({ ...option }))}
              value={stage}
              onChange={(event) => setStage(event.target.value)}
            />
          </div>
          <Textarea
            label="Resume text"
            placeholder="Paste the plain-text version of your resume."
            value={resumeText}
            onChange={(event) => setResumeText(event.target.value)}
            className="min-h-[220px]"
          />
          <Button
            variant="primary"
            loading={isPending}
            disabled={!selectedJob || resumeText.trim().length < 50}
            onClick={handleSubmit}
            icon={<Sparkle size={14} weight="fill" />}
          >
            Generate bundle
          </Button>
        </div>
      </Surface>

      {bundle ? <InterviewPrepBundlePanel bundle={bundle} /> : null}
    </div>
  );
}
