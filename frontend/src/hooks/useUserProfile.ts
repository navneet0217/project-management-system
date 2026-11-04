import { useEffect, useState } from 'react'
import { usersApi } from '../api/users'
import type { UserProfile } from '../types'

// Loads one user's profile; reloads when the id changes. `id` null = nothing to load.
export function useUserProfile(id: number | null) {
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(false)

  useEffect(() => {
    if (id === null) return
    let stale = false
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setLoading(true)
    setError(false)
    setProfile(null)
    usersApi
      .profile(id)
      .then((p) => !stale && setProfile(p))
      .catch(() => !stale && setError(true))
      .finally(() => !stale && setLoading(false))
    return () => {
      stale = true
    }
  }, [id])

  return { profile, loading, error }
}
