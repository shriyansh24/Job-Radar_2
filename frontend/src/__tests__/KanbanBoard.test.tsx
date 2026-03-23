import { render, screen, waitFor } from "@testing-library/react";
import { useDraggable, useDroppable } from "@dnd-kit/core";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import KanbanBoard from "../components/pipeline/KanbanBoard";
import type { Application } from "../api/pipeline";

const APP: Application = {
  id: "app-1",
  job_id: null,
  company_name: "Acme",
  position_title: "Role app-1",
  status: "saved",
  source: "manual",
  applied_at: null,
  offer_at: null,
  rejected_at: null,
  follow_up_at: null,
  reminder_at: null,
  notes: null,
  salary_offered: null,
  created_at: "2026-03-23T00:00:00Z",
  updated_at: "2026-03-23T00:00:00Z",
};
const APP_TITLE = APP.position_title ?? "Role app-1";

function DraggableApplication() {
  const { attributes, listeners, setNodeRef } = useDraggable({ id: APP.id });

  return (
    <button ref={setNodeRef} type="button" {...attributes} {...listeners}>
      {APP_TITLE}
    </button>
  );
}

function DroppableColumn({ id, label }: { id: string; label: string }) {
  const { setNodeRef } = useDroppable({ id });

  return (
    <div ref={setNodeRef} data-testid={`column-${id}`}>
      {label}
    </div>
  );
}

describe("KanbanBoard", () => {
  it("supports keyboard drag transitions", async () => {
    const onDragTransition = vi.fn();
    const user = userEvent.setup();

    render(
      <KanbanBoard onDragTransition={onDragTransition} apps={[APP]}>
        <div>
          <DraggableApplication />
          <DroppableColumn id="saved" label="Saved" />
          <DroppableColumn id="screening" label="Screening" />
        </div>
      </KanbanBoard>,
    );

    const draggable = screen.getByRole("button", { name: APP_TITLE });
    const savedColumn = screen.getByTestId("column-saved");
    const screeningColumn = screen.getByTestId("column-screening");

    vi.spyOn(draggable, "getBoundingClientRect").mockReturnValue(
      new DOMRect(0, 0, 120, 40),
    );
    vi.spyOn(savedColumn, "getBoundingClientRect").mockReturnValue(
      new DOMRect(0, 0, 160, 240),
    );
    vi.spyOn(screeningColumn, "getBoundingClientRect").mockReturnValue(
      new DOMRect(240, 0, 160, 240),
    );

    draggable.focus();

    await user.keyboard("[Space]");
    await user.keyboard("[ArrowRight]");
    await user.keyboard("[Space]");

    await waitFor(() => {
      expect(onDragTransition).toHaveBeenCalledWith(APP.id, "screening");
    });
  });
});
