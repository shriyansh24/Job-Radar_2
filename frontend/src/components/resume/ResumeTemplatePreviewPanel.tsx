import { DownloadSimple, Eye } from "@phosphor-icons/react";
import type { ResumeTemplate } from "../../api/resume";
import { Surface } from "../system/Surface";
import Button from "../ui/Button";
import EmptyState from "../ui/EmptyState";
import Select from "../ui/Select";
import Skeleton from "../ui/Skeleton";

export function ResumeTemplatePreviewPanel({
  templates,
  selectedTemplateId,
  onTemplateChange,
  previewHtml,
  previewLoading,
  exportLoading,
  onExport,
}: {
  templates: ResumeTemplate[];
  selectedTemplateId: string;
  onTemplateChange: (templateId: string) => void;
  previewHtml: string | null;
  previewLoading: boolean;
  exportLoading: boolean;
  onExport: () => void;
}) {
  const selectedTemplate =
    templates.find((template) => template.id === selectedTemplateId) ?? null;
  const hasTemplates = templates.length > 0;

  return (
    <div className="space-y-5">
      <div className="grid gap-4 md:grid-cols-[minmax(0,1fr)_160px]">
        <Select
          label="Template"
          options={templates.map((template) => ({
            value: template.id,
            label: template.name,
          }))}
          value={selectedTemplateId}
          onChange={(event) => onTemplateChange(event.target.value)}
          disabled={!hasTemplates}
          placeholder={hasTemplates ? undefined : "No templates"}
        />
        <div className="flex items-end">
          <Button
            className="w-full"
            variant="secondary"
            loading={exportLoading}
            disabled={!hasTemplates}
            onClick={onExport}
            icon={<DownloadSimple size={14} weight="bold" />}
          >
            Export PDF
          </Button>
        </div>
      </div>

      {!hasTemplates ? (
        <Surface tone="subtle" padding="md">
          <EmptyState
            icon={<Eye size={32} weight="bold" />}
            title="No templates"
            description="Template metadata is not available for this resume yet."
          />
        </Surface>
      ) : null}

      {selectedTemplate ? (
        <Surface tone="subtle" padding="md">
          <div className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-text-muted">
            Template note
          </div>
          <p className="mt-3 text-sm leading-6 text-text-secondary">{selectedTemplate.description}</p>
        </Surface>
      ) : null}

      {previewLoading ? (
        <Surface tone="subtle" padding="md" className="space-y-3">
          <Skeleton variant="text" className="h-4 w-32" />
          <Skeleton variant="rect" className="h-[28rem] w-full" />
        </Surface>
      ) : previewHtml ? (
        <Surface tone="subtle" padding="md">
          <div className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-text-muted">
            Preview
          </div>
          <div
            className="mt-4 max-h-[32rem] overflow-auto border-2 border-border bg-background p-4 text-sm text-text-primary"
            dangerouslySetInnerHTML={{ __html: previewHtml }}
          />
        </Surface>
      ) : (
        <Surface tone="subtle" padding="md">
          <EmptyState
            icon={<Eye size={32} weight="bold" />}
            title="No preview"
            description="Choose a template to load the rendered preview."
          />
        </Surface>
      )}
    </div>
  );
}
