import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import EmptyState from "../../../components/ui/EmptyState";

describe("EmptyState", () => {
  it("renders title", () => {
    render(<EmptyState title="No jobs found" />);
    expect(screen.getByText("No jobs found")).toBeInTheDocument();
  });

  it("renders description when provided", () => {
    render(<EmptyState title="Empty" description="Try adjusting your filters." />);
    expect(screen.getByText("Try adjusting your filters.")).toBeInTheDocument();
  });

  it("does not render description when omitted", () => {
    render(<EmptyState title="Empty" />);
    expect(screen.queryByText(/filter/i)).not.toBeInTheDocument();
  });

  it("renders icon when provided", () => {
    render(<EmptyState title="Empty" icon={<span data-testid="empty-icon" />} />);
    expect(screen.getByTestId("empty-icon")).toBeInTheDocument();
  });

  it("does not render icon slot when not provided", () => {
    render(<EmptyState title="Empty" />);
    // Icon container div should not be rendered at all
    expect(screen.queryByTestId("empty-icon")).not.toBeInTheDocument();
  });

  it("renders action button with label", () => {
    render(<EmptyState title="Empty" action={{ label: "Add Item", onClick: vi.fn() }} />);
    expect(screen.getByRole("button", { name: /add item/i })).toBeInTheDocument();
  });

  it("calls action.onClick when action button is clicked", async () => {
    const handleClick = vi.fn();
    render(<EmptyState title="Empty" action={{ label: "Create", onClick: handleClick }} />);
    await userEvent.click(screen.getByRole("button", { name: /create/i }));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it("does not render action button when action is omitted", () => {
    render(<EmptyState title="Nothing here" />);
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });

  it("forwards className prop", () => {
    const { container } = render(<EmptyState title="Test" className="test-class" />);
    expect(container.firstChild).toHaveClass("test-class");
  });
});
