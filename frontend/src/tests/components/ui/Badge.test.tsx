import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import Badge from "../../../components/ui/Badge";

describe("Badge", () => {
  it("renders children text", () => {
    render(<Badge>Active</Badge>);
    expect(screen.getByText("Active")).toBeInTheDocument();
  });

  it("renders each variant without crashing", () => {
    const variants = ["default", "secondary", "outline", "success", "warning", "danger", "info"] as const;
    for (const variant of variants) {
      const { unmount } = render(<Badge variant={variant}>{variant}</Badge>);
      expect(screen.getByText(variant)).toBeInTheDocument();
      unmount();
    }
  });

  it("renders each size without crashing", () => {
    const { unmount: u1 } = render(<Badge size="sm">Small</Badge>);
    expect(screen.getByText("Small")).toBeInTheDocument();
    u1();

    render(<Badge size="md">Medium</Badge>);
    expect(screen.getByText("Medium")).toBeInTheDocument();
  });

  it("forwards className prop", () => {
    render(<Badge className="my-badge">Tagged</Badge>);
    const badge = screen.getByText("Tagged");
    expect(badge.className).toContain("my-badge");
  });

  it("renders as a span element", () => {
    render(<Badge>Span Badge</Badge>);
    const badge = screen.getByText("Span Badge");
    expect(badge.tagName.toLowerCase()).toBe("span");
  });

  it("uses default variant when none specified", () => {
    render(<Badge>Default</Badge>);
    expect(screen.getByText("Default")).toBeInTheDocument();
  });
});
