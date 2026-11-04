export type Role = 'ADMIN' | 'MANAGER' | 'DEVELOPER'
export type ProjectStatus = 'PLANNING' | 'ACTIVE' | 'ON_HOLD' | 'COMPLETED'
export type TaskStatus = 'TODO' | 'IN_PROGRESS' | 'IN_REVIEW' | 'DONE'
export type Priority = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
export type ActivityType = 'CREATED' | 'STATUS_CHANGED' | 'ASSIGNEE_CHANGED'

export interface UserOption {
  id: number
  full_name: string
  role: Role
}

export interface User extends UserOption {
  email: string
  is_active: boolean
  created_at: string
}

export interface TokenPair {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface Page<T> {
  items: T[]
  total: number
  page: number
  size: number
}

export interface Project {
  id: number
  name: string
  description: string | null
  status: ProjectStatus
  start_date: string | null
  end_date: string | null
  manager: UserOption | null
  member_count: number
  total_tasks: number
  done_tasks: number
  completion_percentage: number
  created_at: string
}

export interface ProjectPayload {
  name?: string
  description?: string | null
  status?: ProjectStatus
  start_date?: string | null
  end_date?: string | null
  manager_id?: number | null
}

export interface Task {
  id: number
  project_id: number
  project_name?: string | null
  title: string
  description: string | null
  status: TaskStatus
  priority: Priority
  deadline: string | null
  assignee: UserOption | null
  created_by: number | null
  created_at: string
  updated_at: string
  is_overdue: boolean
  due_soon: boolean
}

export interface TaskPayload {
  title?: string
  description?: string | null
  priority?: Priority
  deadline?: string | null
  assignee_id?: number | null
}

export interface TaskComment {
  id: number
  task_id: number
  user: UserOption | null
  body: string
  created_at: string
}

export interface TaskActivity {
  id: number
  type: ActivityType
  old_value: string | null
  new_value: string | null
  user: UserOption | null
  created_at: string
}

export interface ProjectProgress {
  id: number
  name: string
  total_tasks: number
  done_tasks: number
  completion_percentage: number
}

export interface DeadlineItem {
  id: number
  title: string
  project_id: number
  project_name: string
  deadline: string
  priority: Priority
  status: TaskStatus
}

export interface Dashboard {
  role: Role
  summary: Record<string, number>
  tasks_by_status: Record<string, number>
  tasks_by_priority: Record<string, number>
  projects: ProjectProgress[]
  upcoming_deadlines: DeadlineItem[]
}

export interface ProjectRef {
  id: number
  name: string
  status: ProjectStatus
}

export interface UserListItem extends User {
  projects: ProjectRef[]
}

export interface ProfileProject extends ProjectRef {
  relation: 'Member' | 'Manager' | 'Removed'
}

export type AuditAction =
  | 'PROJECT_UPDATED'
  | 'TASK_CREATED'
  | 'TASK_UPDATED'
  | 'TASK_DELETED'
  | 'TASK_ASSIGNED'
  | 'TASK_REASSIGNED'
  | 'TASK_STATUS_CHANGED'
  | 'TASK_PRIORITY_CHANGED'
  | 'COMMENT_ADDED'
  | 'MEMBER_ADDED'
  | 'MEMBER_REMOVED'

export type AuditEntity = 'PROJECT' | 'TASK' | 'MEMBER' | 'COMMENT'
export type ActivityCategory = 'tasks' | 'members' | 'project' | 'comments'

export interface ProjectActivity {
  id: number
  project_id: number
  project_name: string | null
  action: AuditAction
  entity_type: AuditEntity
  entity_id: number | null
  entity_label: string | null
  field: string | null
  old_value: string | null
  new_value: string | null
  comment: string | null
  created_at: string
  actor: UserOption | null
  target_user: UserOption | null
}

export interface UserProfile {
  user: User
  managers: UserOption[]
  current_projects: ProfileProject[]
  past_projects: ProfileProject[]
  tasks: Task[]
  activity: ProjectActivity[]
}