import type { TaskListParams } from '../api/tasks'
import type { Sort } from '../hooks/useSort'
import { PRIORITIES, TASK_STATUSES } from './options'
import type { Priority, TaskStatus } from '../types'

export type SortField = NonNullable<TaskListParams['sort_by']>
export type TaskSort = Sort<SortField>

export const TASK_SORT_FIELDS: readonly SortField[] = ['created_at', 'deadline', 'priority', 'status', 'title']

// Reads ?sort_by=&order=&status=&priority= (used by the Dashboard "View all" links) into the table's initial state.
export function taskTableInitial(params: URLSearchParams, fallbackSort?: TaskSort) {
  const field = params.get('sort_by') as SortField | null
  const status = params.get('status') as TaskStatus | null
  const priority = params.get('priority') as Priority | null
  return {
    sort:
      field && TASK_SORT_FIELDS.includes(field)
        ? ({ field, order: params.get('order') === 'asc' ? 'asc' : 'desc' } as TaskSort)
        : fallbackSort,
    status: status && TASK_STATUSES.includes(status) ? status : undefined,
    priority: priority && PRIORITIES.includes(priority) ? priority : undefined,
  }
}
