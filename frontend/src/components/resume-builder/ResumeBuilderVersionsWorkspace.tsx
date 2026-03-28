import { Eye, FileText } from "@phosphor-icons/react";
import type { ResumeVersion } from "../../api/resume";
import { ResumeVersionCard } from "../resume/ResumeWidgets";
import { SplitWorkspace } from "../system/SplitWorkspace";
import { StateBlock } from "../system/StateBlock";
import { Surface } from "../system/Surface";
import EmptyState from "../ui/EmptyState";
import { SkeletonCard } from "../ui/Skeleton";

type ResumeBuilderVersionsWorkspaceProps = {
  isLoading: boolean;
  versions: ResumeVersion[] | undefined;
  onPreview: (version: ResumeVersion) => void;
};

export function ResumeBuilderVersionsWorkspace({
  isLoading,
  versions,
  onPreview,
}: ResumeBuilderVersionsWorkspaceProps) {
  return (
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
              <ResumeVersionCard key={version.id} version={version} onPreview={() => onPreview(version)} />
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
            description="Open a version to inspect parsed text, rendered output, and export templates."
          />
        </div>
      }
    />
  );
}
