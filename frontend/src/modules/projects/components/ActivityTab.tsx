import { useCallback, useEffect, useState } from 'react'
import { Alert, Button, Segmented, Skeleton } from 'antd'
import { projectsApi } from '../api'
import { CATEGORY_OPTIONS } from '../../../lib/activity'
import ActivityTimeline from './ActivityTimeline'
import type { ActivityCategory, ProjectActivity } from '../../../types'

const PAGE_SIZE = 15

// Project Activity tab: filterable audit timeline loaded from the backend, "Load more" for older entries.
export default function ActivityTab({ projectId }: { projectId: number }) {
  const [category, setCategory] = useState<ActivityCategory | 'all'>('all')
  const [items, setItems] = useState<ProjectActivity[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  const load = useCallback(
    async (nextPage: number, reset: boolean) => {
      setLoading(true)
      setError(false)
      try {
        const res = await projectsApi.activities(projectId, {
          category: category === 'all' ? undefined : category,
          page: nextPage,
          size: PAGE_SIZE,
        })
        setItems((prev) => (reset ? res.items : [...prev, ...res.items]))
        setTotal(res.total)
        setPage(nextPage)
      } catch {
        setError(true)
      } finally {
        setLoading(false)
      }
    },
    [projectId, category],
  )

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load(1, true)
  }, [load])

  return (
    <>
      <Segmented
        value={category}
        onChange={(v) => setCategory(v as ActivityCategory | 'all')}
        options={CATEGORY_OPTIONS}
        style={{ marginBottom: 20 }}
      />
      {error ? (
        <Alert
          type="error"
          showIcon
          title="Could not load activity"
          action={<Button onClick={() => load(1, true)}>Retry</Button>}
        />
      ) : loading && items.length === 0 ? (
        <Skeleton active paragraph={{ rows: 6 }} />
      ) : (
        <>
          <ActivityTimeline items={items} />
          {items.length < total && (
            <Button loading={loading} onClick={() => load(page + 1, false)}>
              Load more
            </Button>
          )}
        </>
      )}
    </>
  )
}
