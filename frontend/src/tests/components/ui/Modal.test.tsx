import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import Modal from "../../../components/ui/Modal";

describe("Modal", () => {
  it("renders nothing when open=false", () => {
    render(
      <Modal open={false} onClose={vi.fn()} title="Test Modal">
        <p>Content</p>
      </Modal>
    );
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(screen.queryByText("Content")).not.toBeInTheDocument();
  });

  it("renders dialog when open=true", () => {
    render(
      <Modal open={true} onClose={vi.fn()} title="My Modal">
        <p>Modal content here</p>
      </Modal>
    );
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(screen.getByText("Modal content here")).toBeInTheDocument();
  });

  it("renders title text when provided", () => {
    render(
      <Modal open={true} onClose={vi.fn()} title="Delete Item">
        <p>Are you sure?</p>
      </Modal>
    );
    expect(screen.getByText("Delete Item")).toBeInTheDocument();
  });

  it("sets aria-labelledby when title is provided", () => {
    render(
      <Modal open={true} onClose={vi.fn()} title="Labelled Modal">
        <span>body</span>
      </Modal>
    );
    const dialog = screen.getByRole("dialog");
    expect(dialog.getAttribute("aria-labelledby")).toBeTruthy();
  });

  it("calls onClose when Escape key is pressed", async () => {
    const handleClose = vi.fn();
    render(
      <Modal open={true} onClose={handleClose} title="Escape Test">
        <p>content</p>
      </Modal>
    );
    await userEvent.keyboard("{Escape}");
    expect(handleClose).toHaveBeenCalledTimes(1);
  });

  it("calls onClose when the close (×) button is clicked", async () => {
    const handleClose = vi.fn();
    render(
      <Modal open={true} onClose={handleClose} title="Close Button Test">
        <p>content</p>
      </Modal>
    );
    const closeBtn = screen.getByRole("button", { name: /close modal/i });
    await userEvent.click(closeBtn);
    expect(handleClose).toHaveBeenCalledTimes(1);
  });

  it("renders children inside the dialog", () => {
    render(
      <Modal open={true} onClose={vi.fn()}>
        <button>Action inside modal</button>
      </Modal>
    );
    expect(screen.getByRole("button", { name: /action inside modal/i })).toBeInTheDocument();
  });

  it("has aria-modal=true on dialog element", () => {
    render(
      <Modal open={true} onClose={vi.fn()}>
        <p>body</p>
      </Modal>
    );
    expect(screen.getByRole("dialog")).toHaveAttribute("aria-modal", "true");
  });
});
