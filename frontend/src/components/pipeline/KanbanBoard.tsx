/**
 * Kanban drag-drop wrapper for the Pipeline page.
 *
 * Wraps PipelineColumn components with @dnd-kit DndContext for
 * drag-and-drop status transitions between columns.
 *
 * DEPENDENCY: Requires `@dnd-kit/core` and `@dnd-kit/sortable` to be installed:
 *   npm install @dnd-kit/core @dnd-kit/sortable
 *
 * Until installed, the Pipeline page continues to work with click-based transitions.
 */

import {
  DndContext,
  DragEndEvent,
  DragOverlay,
  DragStartEvent,
  PointerSensor,
  closestCenter,
  useSensor,
  useSensors,
} from "@dnd-kit/core";
import { useState, type ReactNode } from "react";
import type { Application } from "../../api/pipeline";

interface KanbanBoardProps {
  children: ReactNode;
  onDragTransition: (appId: string, newStatus: string) => void;
  apps: Application[];
}

export default function KanbanBoard({ children, onDragTransition, apps }: KanbanBoardProps) {
  const [activeApp, setActiveApp] = useState<Application | null>(null);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: { distance: 8 },
    })
  );

  function handleDragStart(event: DragStartEvent) {
    const app = apps.find((a) => a.id === event.active.id);
    setActiveApp(app ?? null);
  }

  function handleDragEnd(event: DragEndEvent) {
    setActiveApp(null);

    const { active, over } = event;
    if (!over || active.id === over.id) return;

    // The "over" id is the column key (status name)
    const newStatus = String(over.id);
    const appId = String(active.id);

    onDragTransition(appId, newStatus);
  }

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCenter}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
    >
      {children}
      <DragOverlay>
        {activeApp && (
          <div className="w-64 p-3 rounded-[var(--radius-md)] border border-accent-primary bg-bg-secondary shadow-xl opacity-90">
            <p className="text-sm font-medium text-text-primary truncate">
              {activeApp.position_title}
            </p>
            <p className="text-xs text-text-secondary">{activeApp.company_name}</p>
          </div>
        )}
      </DragOverlay>
    </DndContext>
  );
}
