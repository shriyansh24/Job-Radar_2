import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { PageHeader } from "../../../components/system/PageHeader";

describe("PageHeader", () => {
  it("renders title text", () => {
    render(<PageHeader title="Dashboard" />);
    expect(screen.getByRole("heading", { level: 1, name: /dashboard/i })).toBeInTheDocument();
  });

  it("renders description when provided", () => {
    render(<PageHeader title="Jobs" description="Your saved job listings." />);
    expect(screen.getByText("Your saved job listings.")).toBeInTheDocument();
  });

  it("does not render description element when omitted", () => {
    render(<PageHeader title="Jobs" />);
    expect(screen.queryByText(/your saved/i)).not.toBeInTheDocument();
  });

  it("renders eyebrow text when provided", () => {
    render(<PageHeader title="Pipeline" eyebrow="Section" />);
    expect(screen.getByText("Section")).toBeInTheDocument();
  });

  it("renders meta slot when provided", () => {
    render(<PageHeader title="Pipeline" meta={<span data-testid="meta-badge">42</span>} />);
    expect(screen.getByTestId("meta-badge")).toBeInTheDocument();
  });

  it("renders actions slot when provided", () => {
    render(
      <PageHeader
        title="Settings"
        actions={<button>Save changes</button>}
      />
    );
    expect(screen.getByRole("button", { name: /save changes/i })).toBeInTheDocument();
  });

  it("does not render actions area when not provided", () => {
    render(<PageHeader title="Minimal" />);
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });

  it("renders React node title (not just strings)", () => {
    render(<PageHeader title={<span data-testid="node-title">Custom Title Node</span>} />);
    expect(screen.getByTestId("node-title")).toBeInTheDocument();
  });

  it("forwards className prop to root element", () => {
    const { container } = render(<PageHeader title="Test" className="custom-header" />);
    expect(container.firstChild).toHaveClass("custom-header");
  });
});
