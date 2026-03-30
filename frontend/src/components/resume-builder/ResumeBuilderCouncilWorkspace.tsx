import { UsersThree } from "@phosphor-icons/react";
import type { CouncilEvaluation } from "../../api/resume";
import { ResumeCouncilSummary } from "../resume/ResumeWidgets";
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

type ResumeBuilderCouncilWorkspaceProps = {
  resumeOptions: SelectOption[];
  jobOptions: SelectOption[];
  selectedResume: string;
  selectedJob: string;
  onResumeChange: (value: string) => void;
  onJobChange: (value: string) => void;
  councilPending: boolean;
  onRunCouncil: () => void;
  councilResult: CouncilEvaluation | null;
};

export function ResumeBuilderCouncilWorkspace({
  resumeOptions,
  jobOptions,
  selectedResume,
  selectedJob,
  onResumeChange,
  onJobChange,
  councilPending,
  onRunCouncil,
  councilResult,
}: ResumeBuilderCouncilWorkspaceProps) {
  return (
    <SplitWorkspace
      primary={
        <Surface tone="default" padding="lg" radius="xl">
          <SectionHeader
            title="Council"
            description="Run a multi-model review on the selected resume, with optional job context."
          />
          <div className="mt-5 space-y-4">
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
              placeholder="Optional job context"
            />
            <Button
              variant="primary"
              loading={councilPending}
              disabled={!selectedResume}
              onClick={onRunCouncil}
              icon={<UsersThree size={14} weight="bold" />}
            >
              Run council
            </Button>
          </div>

          {councilResult ? (
            <ResumeCouncilSummary
              score={councilResult.overall_score ?? 0}
              evaluations={councilResult.evaluations}
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
            description={
              selectedJob
                ? "Council output will be scored against the selected target role."
                : "Use council feedback to compare models and tune the draft."
            }
          />
        </div>
      }
    />
  );
}
