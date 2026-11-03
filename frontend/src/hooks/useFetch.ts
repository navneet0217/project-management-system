import { useCallback, useEffect, useState } from 'react'

// Small data-loading helper: gives data + loading + error + reload for any API call.
export function useFetch<T>(fetcher: () => Promise<T>) {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    setError(false)
    try {
      setData(await fetcher())
    } catch {
      setError(true)
    } finally {
      setLoading(false)
    }
  }, [fetcher])

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load()
  }, [load])

  return { data, loading, error, reload: load }
}
