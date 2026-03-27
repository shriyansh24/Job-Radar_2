import {
  DndContext,
  DragEndEvent,
  DragOverlay,
  DragStartEvent,
  KeyboardSensor,
  PointerSensor,
  closestCenter,
  defaultKeyboardCoordinateGetter,
  type KeyboardCoordinateGetter,
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

const kanbanKeyboardCoordinates: KeyboardCoordinateGetter = (event, args) => {
  const fallback = defaultKeyboardCoordinateGetter(event, args);
  if (event.code !== "ArrowLeft" && event.code !== "ArrowRight") {
    return fallback;
  }

  const currentId = args.context.over?.id;
  if (currentId == null) {
    return fallback;
  }

  const currentRect = args.context.droppableRects.get(currentId);
  if (!currentRect) {
    return fallback;
  }

  let nextCoordinates: { x: number; y: number } | null = null;
  let nextDistance = Number.POSITIVE_INFINITY;

  for (const container of args.context.droppableContainers.getEnabled()) {
    if (!container || container.id === currentId || container.disabled) {
      continue;
    }
    const rect = args.context.droppableRects.get(container.id);
    if (!rect) {
      continue;
    }

    const delta = rect.left - currentRect.left;
    if (event.code === "ArrowRight" && delta <= 0) {
      continue;
    }
    if (event.code === "ArrowLeft" && delta >= 0) {
      continue;
    }

    const distance = Math.abs(delta);
    if (distance < nextDistance) {
      nextCoordinates = {
        x: rect.left + rect.width / 2,
        y: rect.top + rect.height / 2,
      };
      nextDistance = distance;
    }
  }

  return nextCoordinates ?? fallback;
};

export default function KanbanBoard({ children, onDragTransition, apps }: KanbanBoardProps) {
  const [activeApp, setActiveApp] = useState<Application | null>(null);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: { distance: 8 },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: kanbanKeyboardCoordinates,
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

  function handleDragCancel() {
    setActiveApp(null);
  }

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCenter}
      onDragStart={handleDragStart}
      onDragCancel={handleDragCancel}
      onDragEnd={handleDragEnd}
    >
      {children}
      <DragOverlay dropAnimation={{ duration: 200, easing: "ease" }}>
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
