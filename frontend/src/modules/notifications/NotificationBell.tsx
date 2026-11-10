import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Badge, Button, Empty, List, Popover, Typography } from 'antd'
import { BellOutlined } from '@ant-design/icons'
import { notificationsApi, type AppNotification } from './api'
import { formatDateTime } from '../../lib/dates'

const POLL_MS = 30_000

export default function NotificationBell() {
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const [items, setItems] = useState<AppNotification[]>([])
  const [unread, setUnread] = useState(0)

  const load = useCallback(() => {
    notificationsApi
      .list()
      .then((d) => {
        setItems(d.items)
        setUnread(d.unread)
      })
      .catch(() => undefined) // the bell is best effort; a failed poll must not show an error
  }, [])

  useEffect(() => {
    load()
    const timer = setInterval(load, POLL_MS)
    return () => clearInterval(timer)
  }, [load])

  const openItem = async (n: AppNotification) => {
    if (!n.is_read) await notificationsApi.read(n.id).catch(() => undefined)
    setOpen(false)
    load()
    if (n.project_id) navigate(`/projects/${n.project_id}`)
  }

  const markAll = async () => {
    await notificationsApi.readAll().catch(() => undefined)
    load()
  }

  const content = (
    <div style={{ width: 320, maxWidth: '80vw' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography.Text strong>Notifications</Typography.Text>
        <Button type="link" size="small" disabled={!unread} onClick={markAll}>
          Mark all read
        </Button>
      </div>
      {items.length === 0 ? (
        <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="You are all caught up" />
      ) : (
        <List
          size="small"
          style={{ maxHeight: 360, overflowY: 'auto' }}
          dataSource={items}
          renderItem={(n) => (
            <List.Item onClick={() => openItem(n)} style={{ cursor: 'pointer', opacity: n.is_read ? 0.6 : 1 }}>
              <List.Item.Meta
                title={<span style={{ fontWeight: n.is_read ? 400 : 600 }}>{n.title}</span>}
                description={
                  <>
                    <div>{n.body}</div>
                    <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                      {formatDateTime(n.created_at)}
                    </Typography.Text>
                  </>
                }
              />
            </List.Item>
          )}
        />
      )}
    </div>
  )

  return (
    <Popover
      content={content}
      trigger="click"
      placement="bottomRight"
      open={open}
      onOpenChange={(v) => {
        setOpen(v)
        if (v) load()
      }}
    >
      <Badge count={unread} size="small" offset={[-4, 4]}>
        <Button type="text" shape="circle" aria-label="Notifications" icon={<BellOutlined />} />
      </Badge>
    </Popover>
  )
}
