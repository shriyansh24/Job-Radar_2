import { UploadSimple } from "@phosphor-icons/react";
import type { DropzoneInputProps, DropzoneRootProps } from "react-dropzone";
import { ResumeStatusRail } from "../resume/ResumeWidgets";
import { SplitWorkspace } from "../system/SplitWorkspace";
import { SectionHeader } from "../system/SectionHeader";
import { StateBlock } from "../system/StateBlock";
import { Surface } from "../system/Surface";

type ResumeBuilderUploadWorkspaceProps = {
  rootProps: DropzoneRootProps;
  inputProps: DropzoneInputProps;
  isDragActive: boolean;
  uploadPending: boolean;
  uploadSuccess: boolean;
  versionCount: number;
  selectedResume: string;
};

export function ResumeBuilderUploadWorkspace({
  rootProps,
  inputProps,
  isDragActive,
  uploadPending,
  uploadSuccess,
  versionCount,
  selectedResume,
}: ResumeBuilderUploadWorkspaceProps) {
  return (
    <SplitWorkspace
      primary={
        <Surface tone="default" padding="lg" radius="xl">
          <SectionHeader title="Upload" description="Add a base resume before tailoring or review." />
          <button
            type="button"
            {...rootProps}
            className="hero-panel mt-5 flex w-full flex-col items-center justify-center border-2 border-dashed border-border px-6 py-14 text-center transition-colors"
          >
            <input {...inputProps} />
            <UploadSimple size={40} weight="bold" className="text-text-primary" />
            <p className="mt-5 text-xl font-black uppercase tracking-[-0.05em] text-text-primary">
              {isDragActive ? "Drop the file here" : "Drag and drop a resume"}
            </p>
            <p className="mt-3 text-sm leading-6 text-muted-foreground">or click to browse</p>
            <p className="mt-2 font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
              PDF and DOCX
            </p>
            {uploadPending ? (
              <p className="mt-4 text-sm font-semibold text-accent-primary">Uploading...</p>
            ) : null}
            {uploadSuccess ? (
              <p className="mt-4 text-sm font-semibold text-accent-secondary">Upload complete</p>
            ) : null}
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
          <ResumeStatusRail versionCount={versionCount} selectedResume={selectedResume} />
        </div>
      }
    />
  );
}
