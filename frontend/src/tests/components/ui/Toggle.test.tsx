import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import Toggle from "../../../components/ui/Toggle";

describe("Toggle", () => {
  it("renders a switch button", () => {
    render(<Toggle checked={false} onChange={vi.fn()} />);
    expect(screen.getByRole("switch")).toBeInTheDocument();
  });

  it("sets aria-checked=true when checked", () => {
    render(<Toggle checked={true} onChange={vi.fn()} />);
    expect(screen.getByRole("switch")).toHaveAttribute("aria-checked", "true");
  });

  it("sets aria-checked=false when unchecked", () => {
    render(<Toggle checked={false} onChange={vi.fn()} />);
    expect(screen.getByRole("switch")).toHaveAttribute("aria-checked", "false");
  });

  it("calls onChange with true when toggled from unchecked", async () => {
    const handleChange = vi.fn();
    render(<Toggle checked={false} onChange={handleChange} />);
    await userEvent.click(screen.getByRole("switch"));
    expect(handleChange).toHaveBeenCalledWith(true);
  });

  it("calls onChange with false when toggled from checked", async () => {
    const handleChange = vi.fn();
    render(<Toggle checked={true} onChange={handleChange} />);
    await userEvent.click(screen.getByRole("switch"));
    expect(handleChange).toHaveBeenCalledWith(false);
  });

  it("does not call onChange when disabled", async () => {
    const handleChange = vi.fn();
    render(<Toggle checked={false} onChange={handleChange} disabled />);
    await userEvent.click(screen.getByRole("switch"));
    expect(handleChange).not.toHaveBeenCalled();
  });

  it("button is disabled when disabled prop is set", () => {
    render(<Toggle checked={false} onChange={vi.fn()} disabled />);
    expect(screen.getByRole("switch")).toBeDisabled();
  });

  it("renders label text when provided", () => {
    render(<Toggle checked={false} onChange={vi.fn()} label="Dark mode" />);
    expect(screen.getByText("Dark mode")).toBeInTheDocument();
  });

  it("does not render label when omitted", () => {
    render(<Toggle checked={false} onChange={vi.fn()} />);
    expect(screen.queryByText(/mode/i)).not.toBeInTheDocument();
  });
});
