import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ResumeTemplatePreviewPanel } from "../../../components/resume/ResumeTemplatePreviewPanel";

// Mock the sanitizeHtml utility
vi.mock("../../../lib/sanitize", () => ({
  sanitizeHtml: vi.fn((html) => {
    if (html?.includes("<script>")) {
      return html.replace(/<script>.*?<\/script>/g, "");
    }
    return html;
  }),
}));

const mockTemplates = [
  { id: "1", name: "Template 1", description: "Description 1" },
];

describe("ResumeTemplatePreviewPanel", () => {
  it("renders correctly with preview content", () => {
    const previewHtml = "<div>Test Preview</div>";
    render(
      <ResumeTemplatePreviewPanel
        templates={mockTemplates}
        selectedTemplateId="1"
        onTemplateChange={() => {}}
        previewHtml={previewHtml}
        previewLoading={false}
        exportLoading={false}
        onExport={() => {}}
      />
    );

    expect(screen.getByText("Preview")).toBeDefined();
    expect(screen.getByText("Test Preview")).toBeDefined();
  });

  it("sanitizes HTML content", () => {
    const maliciousHtml = "<div>Safe</div><script>alert('xss')</script>";
    render(
      <ResumeTemplatePreviewPanel
        templates={mockTemplates}
        selectedTemplateId="1"
        onTemplateChange={() => {}}
        previewHtml={maliciousHtml}
        previewLoading={false}
        exportLoading={false}
        onExport={() => {}}
      />
    );

    expect(screen.getByText("Safe")).toBeDefined();
    expect(screen.queryByText("alert('xss')")).toBeNull();
  });
});
