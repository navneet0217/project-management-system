import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios'
import { message } from 'antd'
import type { TokenPair } from '../types'

const BASE_URL = '/api/v1'
export const REFRESH_KEY = 'refresh_token'

// The store is injected from main.tsx so this file does not import the store (avoids a circular import).
interface AuthBridge {
  getAccessToken: () => string | null
  onTokens: (accessToken: string) => void
  onLogout: () => void
}
let bridge: AuthBridge | null = null
export function injectAuthBridge(b: AuthBridge) {
  bridge = b
}

const api = axios.create({ baseURL: BASE_URL })

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = bridge?.getAccessToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

type Retryable = InternalAxiosRequestConfig & { _retry?: boolean }
let refreshPromise: Promise<string> | null = null

// One shared refresh call: parallel 401s wait for the same new token.
function refreshAccessToken(): Promise<string> {
  if (!refreshPromise) {
    const refreshToken = localStorage.getItem(REFRESH_KEY)
    if (!refreshToken) return Promise.reject(new Error('No refresh token'))
    refreshPromise = axios
      .post<TokenPair>(`${BASE_URL}/auth/refresh`, { refresh_token: refreshToken })
      .then(({ data }) => {
        localStorage.setItem(REFRESH_KEY, data.refresh_token)
        bridge?.onTokens(data.access_token)
        return data.access_token
      })
      .finally(() => {
        refreshPromise = null
      })
  }
  return refreshPromise
}

export function errorMessage(error: unknown): string {
  const detail = (error as AxiosError<{ detail?: unknown }>)?.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail.length) {
    return detail.map((d: { msg?: string }) => d.msg).filter(Boolean).join(', ')
  }
  return (error as Error)?.message || 'Something went wrong'
}

api.interceptors.response.use(
  (res) => res,
  async (error: AxiosError) => {
    const original = error.config as Retryable | undefined
    const status = error.response?.status
    const isAuthCall = ['/auth/login', '/auth/refresh', '/auth/logout'].includes(original?.url ?? '')

    if (status === 401 && original && !original._retry && !isAuthCall) {
      original._retry = true
      try {
        const token = await refreshAccessToken()
        original.headers.Authorization = `Bearer ${token}`
        return api(original)
      } catch {
        localStorage.removeItem(REFRESH_KEY)
        bridge?.onLogout()
        return Promise.reject(error)
      }
    }

    // Login errors are shown inside the form; 401s are handled above.
    if (status !== 401) message.error(errorMessage(error))
    return Promise.reject(error)
  },
)

export default api
