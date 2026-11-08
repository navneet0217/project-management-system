import api from './axios'
import type { TokenPair, User } from '../types'

export const authApi = {
  login: (email: string, password: string) =>
    api.post<TokenPair>('/auth/login', { email, password }).then((r) => r.data),
  signup: (data: { email: string; full_name: string; password: string }) =>
    api.post<{ detail: string }>('/auth/signup', data).then((r) => r.data),
  verifyEmail: (token: string) => api.post('/auth/verify-email', { token }),
  resendVerification: (email: string) => api.post('/auth/resend-verification', { email }),
  forgotPassword: (email: string) => api.post('/auth/forgot-password', { email }),
  resetPassword: (token: string, password: string) =>
    api.post('/auth/reset-password', { token, password }),
  logout: (refresh_token: string) => api.post('/auth/logout', { refresh_token }),
  me: () => api.get<User>('/auth/me').then((r) => r.data),
}
