import { FileText } from "@phosphor-icons/react";
import type { DropzoneInputProps, DropzoneRootProps } from "react-dropzone";
import type { ResumeVersion } from "../../api/resume";
import EmptyState from "../ui/EmptyState";
import { SkeletonCard } from "../ui/Skeleton";
import { Surface } from "../system/Surface";
import { SplitWorkspace } from "../system/SplitWorkspace";
import { StateBlock } from "../system/StateBlock";
import { VaultResumeCard, VaultUploadSurface } from "./VaultPanels";

export function VaultResumesTab({
  resumes,
  resumesLoading,
  getRootProps,
  getInputProps,
  isDragActive,
  uploading,
  onPreview,
  onEdit,
  onDelete,
}: {
  resumes: ResumeVersion[] | undefined;
  resumesLoading: boolean;
  getRootProps: () => DropzoneRootProps;
  getInputProps: () => DropzoneInputProps;
  isDragActive: boolean;
  uploading: boolean;
  onPreview: (resume: ResumeVersion) => void;
  onEdit: (resume: ResumeVersion) => void;
  onDelete: (resumeId: string) => void;
}) {
  return (
    <SplitWorkspace
      primary={
        <div className="space-y-6">
          <VaultUploadSurface
            getRootProps={getRootProps}
            getInputProps={getInputProps}
            isDragActive={isDragActive}
            uploading={uploading}
          />

          {resumesLoading ? (
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {Array.from({ length: 3 }).map((_, index) => (
                <SkeletonCard key={index} />
              ))}
            </div>
          ) : !resumes || resumes.length === 0 ? (
            <Surface tone="default" padding="lg" radius="xl" className="brutal-panel">
              <EmptyState
                icon={<FileText size={40} weight="bold" />}
                title="No resumes"
                description="Upload a resume to start the vault."
              />
            </Surface>
          ) : (
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {resumes.map((resume) => (
                <VaultResumeCard
                  key={resume.id}
                  resume={resume}
                  onPreview={() => onPreview(resume)}
                  onEdit={() => onEdit(resume)}
                  onDelete={() => onDelete(resume.id)}
                />
              ))}
            </div>
          )}
        </div>
      }
      secondary={
        <div className="space-y-4">
          <StateBlock
            tone="neutral"
            icon={<FileText size={18} weight="bold" />}
            title="Vault role"
            description="Keep source material stable while downstream surfaces generate variants."
          />
        </div>
      }
    />
  );
}
