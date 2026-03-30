import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import Dropdown from "../../../components/ui/Dropdown";

describe("Dropdown", () => {
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
});
