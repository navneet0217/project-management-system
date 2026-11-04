import { label } from './options'
import type { ActivityCategory, AuditAction, ProjectActivity } from '../types'

const FIELD_LABELS: Record<string, string> = {
  name: 'name',
  description: 'description',
  status: 'status',
  start_date: 'start date',
  end_date: 'end date',
  manager: 'manager',
  title: 'title',
  priority: 'priority',
  deadline: 'deadline',
  assignee: 'assignee',
}

export const CATEGORY_OPTIONS: { value: ActivityCategory | 'all'; label: string }[] = [
  { value: 'all', label: 'All' },
  { value: 'tasks', label: 'Tasks' },
  { value: 'members', label: 'Members' },
  { value: 'project', label: 'Project' },
  { value: 'comments', label: 'Comments' },
]

export const ACTION_COLORS: Record<AuditAction, string> = {
  PROJECT_UPDATED: 'blue',
  TASK_CREATED: 'green',
  TASK_UPDATED: 'blue',
  TASK_DELETED: 'red',
  TASK_ASSIGNED: 'cyan',
  TASK_REASSIGNED: 'cyan',
  TASK_STATUS_CHANGED: 'orange',
  TASK_PRIORITY_CHANGED: 'gold',
  COMMENT_ADDED: 'gray',
  MEMBER_ADDED: 'green',
  MEMBER_REMOVED: 'red',
}

// status/priority values are stored as codes (IN_PROGRESS): show them as words
const pretty = (field: string | null, value: string | null) =>
  value === null ? null : field === 'status' || field === 'priority' ? label(value) : value

export interface ActivityView {
  summary: string
  from?: string | null
  to?: string | null
  hasChange: boolean
  quote?: string | null
}

export function describeActivity(a: ProjectActivity): ActivityView {
  const name = a.entity_label ? `"${a.entity_label}"` : 'a task'
  const field = a.field ? (FIELD_LABELS[a.field] ?? a.field) : ''
  const from = pretty(a.field, a.old_value)
  const to = pretty(a.field, a.new_value)
  const change = { from, to, hasChange: true }
  const plain = { hasChange: false }

  switch (a.action) {
    case 'PROJECT_UPDATED':
      return { summary: `changed the project ${field}`, ...change }
    case 'TASK_CREATED':
      return { summary: `created task ${name}`, ...plain }
    case 'TASK_UPDATED':
      return { summary: `changed the ${field} of task ${name}`, ...change }
    case 'TASK_DELETED':
      return { summary: `deleted task ${name}`, ...plain, quote: a.comment }
    case 'TASK_ASSIGNED':
      return { summary: `assigned task ${name} to ${a.new_value ?? 'someone'}`, ...plain }
    case 'TASK_REASSIGNED':
      return {
        summary: a.new_value ? `reassigned task ${name}` : `unassigned task ${name}`,
        ...change,
        quote: a.comment,
      }
    case 'TASK_STATUS_CHANGED':
      return { summary: `changed the status of task ${name}`, ...change }
    case 'TASK_PRIORITY_CHANGED':
      return { summary: `changed the priority of task ${name}`, ...change }
    case 'COMMENT_ADDED':
      return { summary: `commented on task ${name}`, ...plain, quote: a.new_value }
    case 'MEMBER_ADDED':
      return { summary: `added ${a.entity_label ?? 'a member'} to the project`, ...plain }
    case 'MEMBER_REMOVED':
      return { summary: `removed ${a.entity_label ?? 'a member'} from the project`, ...plain }
  }
}
