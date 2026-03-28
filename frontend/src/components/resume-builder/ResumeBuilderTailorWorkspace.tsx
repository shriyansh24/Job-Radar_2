import { Sparkle, UsersThree } from "@phosphor-icons/react";
import type { ResumeTailorResponse } from "../../api/resume";
import { ResumeTailorResultPanel } from "../resume/ResumeWidgets";
import { SplitWorkspace } from "../system/SplitWorkspace";
import { SectionHeader } from "../system/SectionHeader";
import { StateBlock } from "../system/StateBlock";
import { Surface } from "../system/Surface";
import Button from "../ui/Button";
import Select from "../ui/Select";

type SelectOption = {
  value: string;
  label: string;
};

type ResumeBuilderTailorWorkspaceProps = {
  resumeOptions: SelectOption[];
  jobOptions: SelectOption[];
  selectedResume: string;
  selectedJob: string;
  onResumeChange: (value: string) => void;
  onJobChange: (value: string) => void;
  tailorPending: boolean;
  onTailor: () => void;
  tailorResult: ResumeTailorResponse | null;
};

export function ResumeBuilderTailorWorkspace({
  resumeOptions,
  jobOptions,
  selectedResume,
  selectedJob,
  onResumeChange,
  onJobChange,
  tailorPending,
  onTailor,
  tailorResult,
}: ResumeBuilderTailorWorkspaceProps) {
  return (
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
                onChange={(event) => onResumeChange(event.target.value)}
                placeholder="Select a resume..."
              />
              <Select
                label="Target job"
                options={jobOptions}
                value={selectedJob}
                onChange={(event) => onJobChange(event.target.value)}
                placeholder="Select a job..."
              />
            </div>
            <div className="mt-5">
              <Button
                variant="primary"
                loading={tailorPending}
                disabled={!selectedResume || !selectedJob}
                onClick={onTailor}
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
  );
}
