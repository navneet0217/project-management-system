import api from './axios'
import type { Dashboard } from '../types'

export const dashboardApi = {
  get: () => api.get<Dashboard>('/dashboard').then((r) => r.data),
}
