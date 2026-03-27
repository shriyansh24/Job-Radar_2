import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import StatCard from "../../../components/ui/StatCard";

describe("StatCard", () => {
  it("renders stat card values and positive or negative trend indicators", () => {
    const { rerender } = render(
      <StatCard
        title="Response rate"
        value="42%"
        icon={<span data-testid="stat-icon">icon</span>}
        change={{ value: 12, positive: true }}
      />
    );

    expect(screen.getByText("Response rate")).toBeInTheDocument();
    expect(screen.getByText("42%")).toBeInTheDocument();
    expect(screen.getByTestId("stat-icon")).toBeInTheDocument();
    expect(screen.getByText((_, node) => node?.textContent === "+12%")).toHaveClass(
      "text-accent-success"
    );

    rerender(
      <StatCard
        title="Decline rate"
        value={8}
        icon={<span data-testid="stat-icon-negative">icon</span>}
        change={{ value: 5, positive: false }}
      />
    );

    expect(screen.getByText((_, node) => node?.textContent === "5%")).toHaveClass(
      "text-accent-danger"
    );
    expect(screen.queryByText((_, node) => node?.textContent === "+12%")).not.toBeInTheDocument();
  });
});
