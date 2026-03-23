import { useDraggable } from "@dnd-kit/core";
import { cn } from "../../lib/utils";
import type { Application } from "../../api/pipeline";
import ApplicationCard from "./ApplicationCard";

interface DraggableCardProps {
  app: Application;
  onTransition: (newStatus: string) => void;
  onViewHistory: () => void;
}

export default function DraggableCard({
  app,
  onTransition,
  onViewHistory,
}: DraggableCardProps) {
  const { attributes, listeners, setNodeRef, transform, isDragging } =
    useDraggable({ id: app.id });

  const style = transform
    ? { transform: `translate(${transform.x}px, ${transform.y}px)` }
    : undefined;

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={cn(
        "touch-none transition-opacity duration-150",
        isDragging && "opacity-40"
      )}
      {...listeners}
      {...attributes}
    >
      <ApplicationCard
        app={app}
        onTransition={onTransition}
        onViewHistory={onViewHistory}
      />
    </div>
  );
}
