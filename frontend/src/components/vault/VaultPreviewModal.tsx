import { FileText } from "@phosphor-icons/react";
import type { ResumeVersion } from "../../api/resume";
import Modal from "../ui/Modal";

export function VaultPreviewModal({
  resume,
  onClose,
}: {
  resume: ResumeVersion | null;
  onClose: () => void;
}) {
  return (
    <Modal
      open={!!resume}
      onClose={onClose}
      title={resume?.filename ?? "Resume preview"}
      size="lg"
    >
      {resume?.parsed_text ? (
        <pre className="whitespace-pre-wrap font-mono text-sm text-text-primary">{resume.parsed_text}</pre>
      ) : (
        <div className="flex items-center justify-center gap-3 py-8 text-text-muted">
          <FileText size={20} weight="bold" />
          <span className="text-sm">No parsed text available yet.</span>
        </div>
      )}
    </Modal>
  );
}
