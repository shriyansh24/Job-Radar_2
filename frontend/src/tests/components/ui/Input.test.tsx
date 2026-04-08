import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import Input from "../../../components/ui/Input";

describe("Input", () => {
  it("renders an input element", () => {
    render(<Input />);
    expect(screen.getByRole("textbox")).toBeInTheDocument();
  });

  it("renders label when provided", () => {
    render(<Input label="Email address" />);
    expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
  });

  it("associates label with input via htmlFor/id", () => {
    render(<Input label="Username" id="username-field" />);
    const label = screen.getByText(/username/i);
    const input = screen.getByRole("textbox");
    expect(label).toBeInTheDocument();
    expect(input.id).toBe("username-field");
  });

  it("fires onChange when user types", async () => {
    const handleChange = vi.fn();
    render(<Input onChange={handleChange} />);
    await userEvent.type(screen.getByRole("textbox"), "hello");
    expect(handleChange).toHaveBeenCalled();
  });

  it("renders with controlled value", () => {
    render(<Input value="test value" onChange={vi.fn()} />);
    expect(screen.getByRole("textbox")).toHaveValue("test value");
  });

  it("renders error message below the input", () => {
    render(<Input error="This field is required" />);
    expect(screen.getByText("This field is required")).toBeInTheDocument();
  });

  it("sets aria-invalid when error is provided", () => {
    render(<Input error="Required" />);
    expect(screen.getByRole("textbox")).toHaveAttribute("aria-invalid", "true");
  });

  it("does not set aria-invalid when no error", () => {
    render(<Input />);
    // aria-invalid should not be 'true'
    const input = screen.getByRole("textbox");
    expect(input.getAttribute("aria-invalid")).not.toBe("true");
  });

  it("is disabled when disabled prop is set", () => {
    render(<Input disabled />);
    expect(screen.getByRole("textbox")).toBeDisabled();
  });

  it("renders an icon slot", () => {
    render(<Input icon={<span data-testid="search-icon" />} />);
    expect(screen.getByTestId("search-icon")).toBeInTheDocument();
  });

  it("accepts placeholder prop", () => {
    render(<Input placeholder="Enter email..." />);
    expect(screen.getByPlaceholderText("Enter email...")).toBeInTheDocument();
  });

  it("forwards className to input element", () => {
    render(<Input className="custom-class" />);
    expect(screen.getByRole("textbox").className).toContain("custom-class");
  });
});
