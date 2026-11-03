import { useCallback, useEffect, useState } from 'react'
import {
  DndContext,
  DragOverlay,
  MouseSensor,
  TouchSensor,
  pointerWithin,
  rectIntersection,
  useDraggable,
  useDroppable,
  useSensor,
  useSensors,
  type CollisionDetection,
  type DragEndEvent,
  type DragStartEvent,
} from '@dnd-kit/core'
import { Avatar, Empty, Skeleton, Tag, Tooltip, message } from 'antd'
import { CalendarOutlined } from '@ant-design/icons'
import { tasksApi } from '../api/tasks'
import { errorMessage } from '../api/axios'
import { PRIORITY_COLORS, STATUS_COLORS, TASK_STATUSES, label } from '../lib/options'
import { BRAND } from '../lib/brand'
import type { Task, TaskStatus } from '../types'

// Drop into the column under the cursor; fall back to rectangle overlap (e.g. keyboard/touch edge cases).
const collision: CollisionDetection = (args) => {
  const hits = pointerWithin(args)
  return hits.length ? hits : rectIntersection(args)
}

function CardView({
  task,
  className = '',
  onOpen,
}: {
  task: Task
  className?: string
  onOpen?: (t: Task) => void
}) {
  return (
    <div
      className={`kanban-card ${className}`}
      style={{ borderLeftColor: PRIORITY_COLORS[task.priority] }}
      onClick={() => onOpen?.(task)}
    >
      <div className="kanban-card-title">{task.title}</div>
      <div className="kanban-card-meta">
        <Tag style={{ marginInlineEnd: 0 }}>
          <span style={{ color: PRIORITY_COLORS[task.priority] }}>{label(task.priority)}</span>
        </Tag>
        {task.deadline && (
          <span className={task.is_overdue ? 'due overdue' : 'due'}>
            <CalendarOutlined /> {task.deadline}
          </span>
        )}
        <span style={{ marginLeft: 'auto' }}>
          {task.assignee ? (
            <Tooltip title={task.assignee.full_name}>
              <Avatar size={24} style={{ background: BRAND }}>
                {task.assignee.full_name.charAt(0).toUpperCase()}
              </Avatar>
            </Tooltip>
          ) : (
            <Avatar size={24} style={{ background: '#d9d9d9' }}>
              ?
            </Avatar>
          )}
        </span>
      </div>
    </div>
  )
}

function DraggableCard({
  task,
  draggable,
  onOpen,
}: {
  task: Task
  draggable: boolean
  onOpen: (t: Task) => void
}) {
  const { attributes, listeners, setNodeRef, isDragging } = useDraggable({
    id: task.id,
    disabled: !draggable,
  })
  return (
    <div ref={setNodeRef} {...listeners} {...attributes} style={{ outline: 'none' }}>
      <CardView
        task={task}
        onOpen={onOpen}
        className={`${isDragging ? 'dragging' : ''} ${draggable ? 'movable' : ''}`}
      />
    </div>
  )
}

function Column({
  status,
  tasks,
  canMove,
  onOpen,
}: {
  status: TaskStatus
  tasks: Task[]
  canMove: (t: Task) => boolean
  onOpen: (t: Task) => void
}) {
  const { setNodeRef, isOver } = useDroppable({ id: status })
  return (
    <div className={`kanban-col${isOver ? ' over' : ''}`}>
      <div className="kanban-col-head" style={{ borderTopColor: STATUS_COLORS[status] }}>
        <span>{label(status)}</span>
        <span className="count">{tasks.length}</span>
      </div>
      <div ref={setNodeRef} className="kanban-col-body">
        {tasks.length === 0 ? (
          <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="Drop tasks here" />
        ) : (
          tasks.map((t) => (
            <DraggableCard key={t.id} task={t} draggable={canMove(t)} onOpen={onOpen} />
          ))
        )}
      </div>
    </div>
  )
}

export default function KanbanBoard({
  projectId,
  canMove,
  onOpen,
  onChanged,
  refreshKey,
}: {
  projectId: number
  canMove: (t: Task) => boolean
  onOpen: (t: Task) => void
  onChanged: () => void
  refreshKey: number
}) {
  const [tasks, setTasks] = useState<Task[] | null>(null)
  const [active, setActive] = useState<Task | null>(null)

  const load = useCallback(async () => {
    try {
      setTasks((await tasksApi.listByProject(projectId, { size: 200 })).items)
    } catch {
      setTasks([])
    }
  }, [projectId])

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load()
  }, [load, refreshKey])

  // Click still opens the task; dragging starts after a small move so the two do not clash.
  const sensors = useSensors(
    useSensor(MouseSensor, { activationConstraint: { distance: 6 } }),
    useSensor(TouchSensor, { activationConstraint: { delay: 200, tolerance: 8 } }),
  )

  const onDragStart = (e: DragStartEvent) => {
    setActive(tasks?.find((t) => t.id === e.active.id) ?? null)
  }

  const onDragEnd = async (e: DragEndEvent) => {
    setActive(null)
    const task = tasks?.find((t) => t.id === e.active.id)
    const target = e.over?.id as TaskStatus | undefined
    if (!task || !target || task.status === target) return

    const previous = tasks
    setTasks((cur) => cur!.map((t) => (t.id === task.id ? { ...t, status: target } : t)))
    try {
      await tasksApi.updateStatus(task.id, target)
      message.success(`Moved to ${label(target)}`)
      onChanged()
    } catch (err) {
      setTasks(previous) // server said no: put the card back
      message.error(errorMessage(err))
    }
  }

  if (!tasks) return <Skeleton active paragraph={{ rows: 8 }} />

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={collision}
      onDragStart={onDragStart}
      onDragEnd={onDragEnd}
    >
      <div className="kanban">
        {TASK_STATUSES.map((s) => (
          <Column
            key={s}
            status={s}
            tasks={tasks.filter((t) => t.status === s)}
            canMove={canMove}
            onOpen={onOpen}
          />
        ))}
      </div>
      <DragOverlay>{active && <CardView task={active} className="overlay" />}</DragOverlay>
    </DndContext>
  )
}
