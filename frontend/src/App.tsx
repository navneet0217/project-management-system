import { lazy, Suspense, useEffect } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { App as AntApp, ConfigProvider, Spin, theme } from 'antd'
import { useAppSelector } from './store'
import ProtectedRoute from './routes/ProtectedRoute'
import RedirectIfAuthed from './routes/RedirectIfAuthed'
import AppLayout from './layouts/AppLayout'
import { BRAND } from './lib/brand'

// Pages load on demand, so the first screen downloads far less JavaScript.
const Login = lazy(() => import('./modules/auth/pages/Login'))
const Signup = lazy(() => import('./modules/auth/pages/Signup'))
// Forgot/reset password is switched off for now (re-enable later):
// const ForgotPassword = lazy(() => import('./modules/auth/pages/ForgotPassword'))
// const ResetPassword = lazy(() => import('./modules/auth/pages/ResetPassword'))
const VerifyEmail = lazy(() => import('./modules/auth/pages/VerifyEmail'))
const Dashboard = lazy(() => import('./modules/dashboard/pages/Dashboard'))
const Projects = lazy(() => import('./modules/projects/pages/Projects'))
const ProjectDetail = lazy(() => import('./modules/projects/pages/ProjectDetail'))
const MyTasks = lazy(() => import('./modules/tasks/pages/MyTasks'))
const Tasks = lazy(() => import('./modules/tasks/pages/Tasks'))
const Users = lazy(() => import('./modules/users/pages/Users'))

function ThemedBody({ dark }: { dark: boolean }) {
  const { token } = theme.useToken()
  useEffect(() => {
    document.body.style.background = token.colorBgLayout
    document.documentElement.style.colorScheme = dark ? 'dark' : 'light'
    document.documentElement.dataset.theme = dark ? 'dark' : 'light'
  }, [token.colorBgLayout, dark])
  return null
}

// Same teal brand in both modes; dark mode uses one cohesive teal-tinted palette instead of pure black.
const DARK_TOKENS = {
  colorBgBase: '#0b1517',
  colorBgLayout: '#081012',
  colorBgContainer: '#0f1d20',
  colorBgElevated: '#13262a',
  colorBorder: '#1f3a3f',
  colorBorderSecondary: '#18303a',
}

export default function App() {
  const darkMode = useAppSelector((s) => s.ui.darkMode)

  return (
    <ConfigProvider
      theme={{
        algorithm: darkMode ? theme.darkAlgorithm : theme.defaultAlgorithm,
        token: {
          colorPrimary: BRAND,
          colorLink: BRAND,
          colorInfo: BRAND,
          borderRadius: 10,
          fontFamily:
            "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif",
          ...(darkMode ? DARK_TOKENS : { colorBgLayout: '#f1f5f5' }),
        },
        components: {
          Card: { borderRadiusLG: 16 },
          Button: { fontWeight: 500 },
          // Roomy sidebar items
          Menu: {
            itemHeight: 48,
            fontSize: 15,
            iconSize: 19,
            itemMarginInline: 10,
            itemMarginBlock: 4,
            itemBorderRadius: 10,
            darkItemBg: 'transparent',
            darkSubMenuItemBg: 'transparent',
            darkItemSelectedBg: 'rgba(255,255,255,0.16)',
            darkItemHoverBg: 'rgba(255,255,255,0.08)',
          },
        },
      }}
    >
      <ThemedBody dark={darkMode} />
      <AntApp>
        <BrowserRouter>
          <Suspense fallback={<Spin fullscreen size="large" />}>
            <Routes>
              <Route path="/login" element={<RedirectIfAuthed><Login /></RedirectIfAuthed>} />
              <Route path="/signup" element={<RedirectIfAuthed><Signup /></RedirectIfAuthed>} />
              {/* <Route path="/forgot-password" element={<ForgotPassword />} /> */}
              {/* <Route path="/reset-password" element={<ResetPassword />} /> */}
              <Route path="/verify-email" element={<VerifyEmail />} />
              <Route element={<ProtectedRoute />}>
                <Route element={<AppLayout />}>
                  <Route index element={<Dashboard />} />
                  <Route path="projects" element={<Projects />} />
                  <Route path="projects/:id" element={<ProjectDetail />} />
                  <Route path="my-tasks" element={<MyTasks />} />
                  <Route element={<ProtectedRoute allowedRoles={['ADMIN', 'MANAGER']} />}>
                    <Route path="tasks" element={<Tasks />} />
                  </Route>
                  <Route element={<ProtectedRoute allowedRoles={['ADMIN']} />}>
                    <Route path="users" element={<Users />} />
                  </Route>
                </Route>
              </Route>
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </Suspense>
        </BrowserRouter>
      </AntApp>
    </ConfigProvider>
  )
}
