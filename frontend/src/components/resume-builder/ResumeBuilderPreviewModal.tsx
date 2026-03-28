import { FileText } from "@phosphor-icons/react";
import type { ResumePreview, ResumeTemplate, ResumeVersion } from "../../api/resume";
import { ResumeTemplatePreviewPanel } from "../resume/ResumeTemplatePreviewPanel";
import { Surface } from "../system/Surface";
import Modal from "../ui/Modal";

type ResumeBuilderPreviewModalProps = {
  showPreview: ResumeVersion | null;
  templates: ResumeTemplate[];
  selectedTemplateId: string;
  onTemplateChange: (value: string) => void;
  previewData: ResumePreview | undefined;
  previewLoading: boolean;
  exportLoading: boolean;
  onClose: () => void;
  onExport: () => void;
};

export function ResumeBuilderPreviewModal({
  showPreview,
  templates,
  selectedTemplateId,
  onTemplateChange,
  previewData,
  previewLoading,
  exportLoading,
  onClose,
  onExport,
}: ResumeBuilderPreviewModalProps) {
  return (
    <Modal
      open={!!showPreview}
      onClose={onClose}
      title={showPreview?.filename ?? "Resume preview"}
      size="xl"
    >
      <div className="grid gap-6 xl:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
        <Surface tone="default" padding="md" radius="xl">
          <div className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-text-muted">
            Parsed text
          </div>
          {showPreview?.parsed_text ? (
            <pre className="mt-4 whitespace-pre-wrap font-mono text-sm text-text-primary">
              {showPreview.parsed_text}
            </pre>
          ) : (
            <div className="flex items-center justify-center gap-3 py-8 text-text-muted">
              <FileText size={20} weight="bold" />
              <span className="text-sm">No parsed text available yet.</span>
            </div>
          )}
        </Surface>

        <ResumeTemplatePreviewPanel
          templates={templates}
          selectedTemplateId={selectedTemplateId}
          onTemplateChange={onTemplateChange}
          previewHtml={previewData?.html ?? null}
          previewLoading={previewLoading}
          exportLoading={exportLoading}
          onExport={onExport}
        />
      </div>
    </Modal>
  );
}
