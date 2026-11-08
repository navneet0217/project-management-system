import api from '../../api/axios'
import type {
  ActivityCategory,
  Page,
  Project,
  ProjectActivity,
  ProjectPayload,
  ProjectStatus,
  UserOption,
} from '../../types'

export interface ProjectListParams {
  search?: string
  status?: ProjectStatus
  page?: number
  size?: number
}

export interface ActivityParams {
  category?: ActivityCategory
  page?: number
  size?: number
}

export const projectsApi = {
  activities: (id: number, params: ActivityParams) =>
    api.get<Page<ProjectActivity>>(`/projects/${id}/activities`, { params }).then((r) => r.data),
  list: (params: ProjectListParams) =>
    api.get<Page<Project>>('/projects', { params }).then((r) => r.data),
  get: (id: number) => api.get<Project>(`/projects/${id}`).then((r) => r.data),
  create: (data: ProjectPayload) => api.post<Project>('/projects', data).then((r) => r.data),
  update: (id: number, data: ProjectPayload) =>
    api.patch<Project>(`/projects/${id}`, data).then((r) => r.data),
  remove: (id: number) => api.delete(`/projects/${id}`),
  members: (id: number) =>
    api.get<UserOption[]>(`/projects/${id}/members`).then((r) => r.data),
  addMember: (id: number, user_id: number) =>
    api.post(`/projects/${id}/members`, { user_id }),
  removeMember: (id: number, userId: number) =>
    api.delete(`/projects/${id}/members/${userId}`),
}
