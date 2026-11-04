import api from './axios'
import type { Page, Role, User, UserListItem, UserOption, UserProfile } from '../types'

export type UserSortField = 'full_name' | 'email' | 'role' | 'is_active' | 'created_at'

export interface UserListParams {
  search?: string
  role?: Role
  is_active?: boolean
  sort_by?: UserSortField
  order?: 'asc' | 'desc'
  page?: number
  size?: number
}

export interface UserCreatePayload {
  email: string
  full_name: string
  password: string
  role: Role
}

export interface UserUpdatePayload {
  full_name?: string
  role?: Role
  is_active?: boolean
  password?: string
}

export const usersApi = {
  list: (params: UserListParams) =>
    api.get<Page<UserListItem>>('/users', { params }).then((r) => r.data),
  profile: (id: number) => api.get<UserProfile>(`/users/${id}/profile`).then((r) => r.data),
  create: (data: UserCreatePayload) => api.post<User>('/users', data).then((r) => r.data),
  update: (id: number, data: UserUpdatePayload) =>
    api.patch<User>(`/users/${id}`, data).then((r) => r.data),
  options: (role?: Role) =>
    api.get<UserOption[]>('/users/options', { params: { role } }).then((r) => r.data),
}
