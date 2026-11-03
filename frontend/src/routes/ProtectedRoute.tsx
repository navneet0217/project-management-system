import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { Spin } from 'antd'
import { useAppSelector } from '../store'
import type { Role } from '../types'

export default function ProtectedRoute({ allowedRoles }: { allowedRoles?: Role[] }) {
  const { user, initialized } = useAppSelector((s) => s.auth)
  const location = useLocation()

  if (!initialized) {
    return <Spin fullscreen size="large" />
  }
  if (!user) return <Navigate to="/login" state={{ from: location }} replace />
  if (allowedRoles && !allowedRoles.includes(user.role)) return <Navigate to="/" replace />
  return <Outlet />
}
