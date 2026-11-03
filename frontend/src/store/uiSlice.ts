import { createSlice, type PayloadAction } from '@reduxjs/toolkit'

const KEY = 'theme'

interface UiState {
  darkMode: boolean
  siderCollapsed: boolean
}

const initialState: UiState = {
  darkMode: localStorage.getItem(KEY) === 'dark',
  siderCollapsed: false,
}

const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    toggleDarkMode(state) {
      state.darkMode = !state.darkMode
      localStorage.setItem(KEY, state.darkMode ? 'dark' : 'light')
    },
    setSiderCollapsed(state, action: PayloadAction<boolean>) {
      state.siderCollapsed = action.payload
    },
  },
})

export const { toggleDarkMode, setSiderCollapsed } = uiSlice.actions
export default uiSlice.reducer
