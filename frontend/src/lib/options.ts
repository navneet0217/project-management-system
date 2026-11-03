export const PROJECT_STATUSES = ['PLANNING', 'ACTIVE', 'ON_HOLD', 'COMPLETED'] as const
export const TASK_STATUSES = ['TODO', 'IN_PROGRESS', 'IN_REVIEW', 'DONE'] as const
export const PRIORITIES = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'] as const
export const ROLES = ['ADMIN', 'MANAGER', 'DEVELOPER'] as const

export const TAG_COLORS: Record<string, string> = {
  PLANNING: 'default',
  ACTIVE: 'processing',
  ON_HOLD: 'warning',
  COMPLETED: 'success',
  TODO: 'default',
  IN_PROGRESS: 'processing',
  IN_REVIEW: 'gold',
  DONE: 'success',
  LOW: 'default',
  MEDIUM: 'blue',
  HIGH: 'orange',
  CRITICAL: 'red',
  ADMIN: 'red',
  MANAGER: 'geekblue',
  DEVELOPER: 'green',
}

// Accent colour per task status (Kanban columns, charts)
export const STATUS_COLORS: Record<string, string> = {
  TODO: '#8c8c8c',
  IN_PROGRESS: '#1677ff',
  IN_REVIEW: '#d97706',
  DONE: '#52c41a',
}

export const PRIORITY_COLORS: Record<string, string> = {
  LOW: '#8c8c8c',
  MEDIUM: '#1677ff',
  HIGH: '#fa8c16',
  CRITICAL: '#f5222d',
}

export const label = (v: string) => v.charAt(0) + v.slice(1).toLowerCase().replace(/_/g, ' ')

export const toOptions = (values: readonly string[]) =>
  values.map((v) => ({ value: v, label: label(v) }))
