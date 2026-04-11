import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ResumeTemplatePreviewPanel } from "../../../components/resume/ResumeTemplatePreviewPanel";

const templates = [
  {
    id: "professional",
    name: "Professional",
    description: "Clean, traditional single-column layout with subtle dividers.",
  },
];

describe("ResumeTemplatePreviewPanel", () => {
  it("renders sanitized preview HTML while preserving template styles", () => {
    const previewHtml = `
      <!DOCTYPE html>
      <html lang="en">
        <head>
          <style>.resume-title { color: rgb(12, 34, 56); }</style>
        </head>
        <body>
          <div class="resume-title">Preview body</div>
          <img src="x" onerror="window.__xss = true" alt="avatar" />
          <script>window.__xss = true</script>
        </body>
      </html>
    `;

    const { container } = render(
      <ResumeTemplatePreviewPanel
        templates={templates}
        selectedTemplateId="professional"
        onTemplateChange={vi.fn()}
        previewHtml={previewHtml}
        previewLoading={false}
        exportLoading={false}
        onExport={vi.fn()}
      />
    );

    expect(screen.getByText("Preview")).toBeInTheDocument();
    expect(screen.getByText("Preview body")).toBeInTheDocument();
    expect(container.querySelector("style")).not.toBeNull();
    expect(container.querySelector("script")).toBeNull();

    const image = container.querySelector("img");
    expect(image).not.toBeNull();
    expect(image?.getAttribute("onerror")).toBeNull();
  });
});
