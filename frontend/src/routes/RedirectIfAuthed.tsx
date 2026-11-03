import { Navigate, useLocation } from 'react-router-dom'
import { useAppSelector } from '../store'

// Logged-in users skip the login/signup pages and go back to where they came from.
export default function RedirectIfAuthed({ children }: { children: React.ReactNode }) {
  const user = useAppSelector((s) => s.auth.user)
  const location = useLocation()
  const from = (location.state as { from?: { pathname: string } } | null)?.from?.pathname ?? '/'
  return user ? <Navigate to={from} replace /> : <>{children}</>
}
