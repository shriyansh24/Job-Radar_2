import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import Card from "../../../components/ui/Card";

describe("Card", () => {
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
});
