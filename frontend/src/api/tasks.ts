import api from './axios'
import type {
  Page,
  Priority,
  Task,
  TaskActivity,
  TaskComment,
  TaskPayload,
  TaskStatus,
} from '../types'

export interface TaskListParams {
  status?: TaskStatus
  priority?: Priority
  assignee_id?: number
  search?: string
  sort_by?: 'created_at' | 'deadline' | 'priority' | 'status' | 'title'
  order?: 'asc' | 'desc'
  page?: number
  size?: number
}

export const tasksApi = {
  listByProject: (projectId: number, params: TaskListParams) =>
    api.get<Page<Task>>(`/projects/${projectId}/tasks`, { params }).then((r) => r.data),
  create: (projectId: number, data: TaskPayload) =>
    api.post<Task>(`/projects/${projectId}/tasks`, data).then((r) => r.data),
  my: (params: TaskListParams) =>
    api.get<Page<Task>>('/tasks/my', { params }).then((r) => r.data),
  update: (id: number, data: TaskPayload) =>
    api.patch<Task>(`/tasks/${id}`, data).then((r) => r.data),
  updateStatus: (id: number, status: TaskStatus) =>
    api.patch<Task>(`/tasks/${id}/status`, { status }).then((r) => r.data),
  remove: (id: number) => api.delete(`/tasks/${id}`),
  comments: (id: number) =>
    api.get<TaskComment[]>(`/tasks/${id}/comments`).then((r) => r.data),
  addComment: (id: number, body: string) =>
    api.post<TaskComment>(`/tasks/${id}/comments`, { body }).then((r) => r.data),
  activities: (id: number) =>
    api.get<TaskActivity[]>(`/tasks/${id}/activities`).then((r) => r.data),
}
