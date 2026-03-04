import { useState } from 'react'
import {
  DndContext,
  closestCenter,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from '@dnd-kit/core'
import {
  SortableContext,
  verticalListSortingStrategy,
  useSortable,
} from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import type { Job } from '../../api/client'
import { PIPELINE_COLUMNS, PIPELINE_LABELS } from '../../lib/constants'
import KanbanCard from './KanbanCard'
import { cn } from '../../lib/utils'

interface KanbanBoardProps {
  jobs: Job[]
  onMoveJob: (jobId: string, newStatus: string) => void
}

function SortableCard({ job }: { job: Job }) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: job.job_id,
    data: { status: job.status },
  })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  }

  return (
    <div ref={setNodeRef} style={style} {...attributes} {...listeners}>
      <KanbanCard job={job} />
    </div>
  )
}

export default function KanbanBoard({ jobs, onMoveJob }: KanbanBoardProps) {
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } })
  )

  const columnJobs = PIPELINE_COLUMNS.reduce(
    (acc, col) => {
      acc[col] = jobs.filter((j) => j.status === col)
      return acc
    },
    {} as Record<string, Job[]>
  )

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event
    if (!over) return

    const jobId = active.id as string
    const overData = over.data.current as { status?: string } | undefined

    // Determine target column
    let targetStatus: string | undefined
    if (overData?.status) {
      targetStatus = overData.status
    } else {
      // Dropped on a column droppable
      targetStatus = over.id as string
    }

    if (targetStatus) {
      const currentJob = jobs.find((j) => j.job_id === jobId)
      if (currentJob && currentJob.status !== targetStatus) {
        onMoveJob(jobId, targetStatus)
      }
    }
  }

  return (
    <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
      <div className="flex gap-4 h-full overflow-x-auto pb-4">
        {PIPELINE_COLUMNS.map((col) => (
          <div key={col} className="flex-shrink-0 w-[260px] flex flex-col">
            {/* Column header */}
            <div className="flex items-center justify-between mb-3 px-1">
              <h3 className="text-xs font-semibold text-text-secondary uppercase">
                {PIPELINE_LABELS[col]}
              </h3>
              <span className="text-xs font-mono text-text-secondary bg-elevated px-1.5 py-0.5 rounded">
                {columnJobs[col]?.length || 0}
              </span>
            </div>

            {/* Column body */}
            <div className="flex-1 bg-elevated/30 rounded-xl p-2 space-y-2 overflow-y-auto min-h-[200px]">
              <SortableContext
                items={(columnJobs[col] || []).map((j) => j.job_id)}
                strategy={verticalListSortingStrategy}
              >
                {columnJobs[col]?.length ? (
                  columnJobs[col].map((job) => (
                    <SortableCard key={job.job_id} job={job} />
                  ))
                ) : (
                  <div className="flex items-center justify-center h-24 border-2 border-dashed border-border rounded-lg">
                    <span className="text-xs text-text-secondary">Drop here</span>
                  </div>
                )}
              </SortableContext>
            </div>
          </div>
        ))}
      </div>
    </DndContext>
  )
}
