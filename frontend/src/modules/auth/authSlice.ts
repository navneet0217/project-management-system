import { createAsyncThunk, createSlice, type PayloadAction } from '@reduxjs/toolkit'
import { authApi } from './api'
import { REFRESH_KEY } from '../../api/axios'
import type { TokenPair, User } from '../../types'

interface AuthState {
  accessToken: string | null
  user: User | null
  // 'loading' until the first session restore attempt finishes
  initialized: boolean
}

const initialState: AuthState = { accessToken: null, user: null, initialized: false }

async function startSession(tokens: TokenPair, dispatch: (a: unknown) => unknown) {
  localStorage.setItem(REFRESH_KEY, tokens.refresh_token)
  dispatch(authSlice.actions.setAccessToken(tokens.access_token))
  return authApi.me()
}

export const login = createAsyncThunk(
  'auth/login',
  async (cred: { email: string; password: string }, { dispatch }) =>
    startSession(await authApi.login(cred.email, cred.password), dispatch),
)

// Restore the session on page load using the stored refresh token.
// The axios 401 interceptor does the refresh, so we just call /auth/me.
export const restoreSession = createAsyncThunk('auth/restore', async () => {
  if (!localStorage.getItem(REFRESH_KEY)) return null
  return authApi.me()
})

export const logout = createAsyncThunk('auth/logout', async () => {
  const refresh = localStorage.getItem(REFRESH_KEY)
  localStorage.removeItem(REFRESH_KEY)
  if (refresh) {
    try {
      await authApi.logout(refresh)
    } catch {
      // the local session is cleared either way
    }
  }
})

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    setAccessToken(state, action: PayloadAction<string>) {
      state.accessToken = action.payload
    },
    clearAuth(state) {
      state.accessToken = null
      state.user = null
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(login.fulfilled, (state, action) => {
        state.user = action.payload
      })
      .addCase(restoreSession.fulfilled, (state, action) => {
        state.user = action.payload
        state.initialized = true
      })
      .addCase(restoreSession.rejected, (state) => {
        state.accessToken = null
        state.user = null
        state.initialized = true
      })
      .addCase(logout.fulfilled, (state) => {
        state.accessToken = null
        state.user = null
      })
  },
})

export const { setAccessToken, clearAuth } = authSlice.actions
export default authSlice.reducer
