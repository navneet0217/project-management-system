import { useEffect, useState } from 'react'
import { Alert, Button, Empty, Modal, Skeleton } from 'antd'

// Centered popup that loads a short list when opened, with a "View all" link at the top-right.
export default function RecentModal<T extends { id: number }>({
  open,
  title,
  onClose,
  onViewAll,
  load,
  renderItem,
  emptyText,
}: {
  open: boolean
  title: string
  onClose: () => void
  onViewAll: () => void
  load: () => Promise<T[]>
  renderItem: (item: T) => React.ReactNode
  emptyText: string
}) {
  const [items, setItems] = useState<T[] | null>(null)
  const [error, setError] = useState(false)

  useEffect(() => {
    if (!open) return
    let stale = false
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setItems(null)
    setError(false)
    load()
      .then((rows) => !stale && setItems(rows))
      .catch(() => !stale && setError(true))
    return () => {
      stale = true
    }
    // reload only when the popup opens
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open])

  return (
    <Modal
      open={open}
      onCancel={onClose}
      footer={null}
      centered
      width={560}
      destroyOnHidden
      title={
        <div className="recent-title">
          <span>{title}</span>
          <Button type="link" onClick={onViewAll}>
            View all
          </Button>
        </div>
      }
    >
      {error ? (
        <Alert type="error" showIcon title="Could not load data" />
      ) : items === null ? (
        <Skeleton active paragraph={{ rows: 5 }} />
      ) : items.length === 0 ? (
        <Empty description={emptyText} />
      ) : (
        <div className="recent-list">
          {items.map((item) => (
            <div key={item.id}>{renderItem(item)}</div>
          ))}
        </div>
      )}
    </Modal>
  )
}
