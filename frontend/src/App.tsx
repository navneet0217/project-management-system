import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { App as AntApp, ConfigProvider, theme } from 'antd'
import { useAppSelector } from './store'
import ProtectedRoute from './routes/ProtectedRoute'
import AppLayout from './layouts/AppLayout'
import Login from './pages/Login'
import Signup from './pages/Signup'
import RedirectIfAuthed from './routes/RedirectIfAuthed'
import Dashboard from './pages/Dashboard'
import Projects from './pages/Projects'
import ProjectDetail from './pages/ProjectDetail'
import MyTasks from './pages/MyTasks'
import Users from './pages/Users'

export default function App() {
  const darkMode = useAppSelector((s) => s.ui.darkMode)

  return (
    <ConfigProvider
      theme={{ algorithm: darkMode ? theme.darkAlgorithm : theme.defaultAlgorithm }}
    >
      <AntApp>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<RedirectIfAuthed><Login /></RedirectIfAuthed>} />
            <Route path="/signup" element={<RedirectIfAuthed><Signup /></RedirectIfAuthed>} />
            <Route element={<ProtectedRoute />}>
              <Route element={<AppLayout />}>
                <Route index element={<Dashboard />} />
                <Route path="projects" element={<Projects />} />
                <Route path="projects/:id" element={<ProjectDetail />} />
                <Route path="my-tasks" element={<MyTasks />} />
                <Route element={<ProtectedRoute allowedRoles={['ADMIN']} />}>
                  <Route path="users" element={<Users />} />
                </Route>
              </Route>
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </AntApp>
    </ConfigProvider>
  )
}
