import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { Provider } from 'react-redux'
import './index.css'
import App from './App'
import { store } from './store'
import { clearAuth, restoreSession, setAccessToken } from './store/authSlice'
import { injectAuthBridge } from './api/axios'

injectAuthBridge({
  getAccessToken: () => store.getState().auth.accessToken,
  onTokens: (token) => store.dispatch(setAccessToken(token)),
  onLogout: () => store.dispatch(clearAuth()),
})

store.dispatch(restoreSession())

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <Provider store={store}>
      <App />
    </Provider>
  </StrictMode>,
)
