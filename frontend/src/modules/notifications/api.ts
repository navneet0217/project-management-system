import api from '../../api/axios'

export interface AppNotification {
  id: number
  project_id: number | null
  title: string
  body: string
  is_read: boolean
  created_at: string
}

export const notificationsApi = {
  list: () => api.get<{ items: AppNotification[]; unread: number }>('/notifications').then((r) => r.data),
  read: (id: number) => api.post(`/notifications/${id}/read`),
  readAll: () => api.post('/notifications/read-all'),
}
