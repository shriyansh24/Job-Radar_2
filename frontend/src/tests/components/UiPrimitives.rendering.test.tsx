import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import Card from "../../components/ui/Card";
import Dropdown from "../../components/ui/Dropdown";
import StatCard from "../../components/ui/StatCard";

describe("UI primitives rendering", () => {
  it("renders card padding variants and handles click affordance", () => {
    const onClick = vi.fn();

    const { rerender } = render(
      <Card hover padding="lg" className="custom-card" onClick={onClick}>
        Card content
      </Card>
    );

    const clickableCard = screen.getByText("Card content").closest("div");
    expect(clickableCard).toHaveClass("card-hover", "cursor-pointer", "p-8", "custom-card");

    fireEvent.click(clickableCard!);
    expect(onClick).toHaveBeenCalledTimes(1);

    rerender(<Card padding="sm">Compact card</Card>);
    expect(screen.getByText("Compact card").closest("div")).toHaveClass("p-4");

    rerender(<Card padding="none">Flush card</Card>);
    expect(screen.getByText("Flush card").closest("div")).not.toHaveClass("p-4", "p-6", "p-8");
  });

  it("opens dropdowns, selects items, and closes on outside clicks", () => {
    const onSelect = vi.fn();

    render(
      <div>
        <Dropdown
          trigger={<button type="button">Open menu</button>}
          align="right"
          onSelect={onSelect}
          items={[
            { label: "Open profile", value: "profile" },
            { label: "Delete", value: "delete", danger: true },
          ]}
        />
        <button type="button">Outside target</button>
      </div>
    );

    expect(screen.queryByRole("button", { name: "Delete" })).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Open menu" }));
    const deleteButton = screen.getByRole("button", { name: "Delete" });
    expect(deleteButton).toHaveClass("text-accent-danger");

    fireEvent.click(screen.getByRole("button", { name: "Open profile" }));
    expect(onSelect).toHaveBeenCalledWith("profile");
    expect(screen.queryByRole("button", { name: "Delete" })).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Open menu" }));
    expect(screen.getByRole("button", { name: "Delete" })).toBeInTheDocument();
    fireEvent.mouseDown(screen.getByRole("button", { name: "Outside target" }));
    expect(screen.queryByRole("button", { name: "Delete" })).not.toBeInTheDocument();
  });

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
