import { useCallback, useState } from 'react'
import { Button, Drawer, Empty, Input, List, Tabs, Timeline, Typography } from 'antd'
import { tasksApi } from '../api/tasks'
import { useFetch } from '../hooks/useFetch'
import QueryState from './QueryState'
import { StatusTag } from './StatusTag'
import { label } from '../lib/options'
import { formatDateTime } from '../lib/dates'
import type { Task, TaskActivity } from '../types'

const describe = (a: TaskActivity) => {
  const who = a.user?.full_name ?? 'Someone'
  if (a.type === 'CREATED') return `${who} created the task`
  if (a.type === 'STATUS_CHANGED') {
    return `${who} moved it from ${label(a.old_value ?? '?')} to ${label(a.new_value ?? '?')}`
  }
  return `${who} changed the assignee: ${a.old_value ?? 'none'} → ${a.new_value ?? 'none'}`
}

function Comments({ taskId }: { taskId: number }) {
  const fetcher = useCallback(() => tasksApi.comments(taskId), [taskId])
  const { data, loading, error, reload } = useFetch(fetcher)
  const [body, setBody] = useState('')
  const [sending, setSending] = useState(false)

  const send = async () => {
    if (!body.trim()) return
    setSending(true)
    try {
      await tasksApi.addComment(taskId, body.trim())
      setBody('')
      reload()
    } catch {
      // error toast comes from the axios interceptor
    } finally {
      setSending(false)
    }
  }

  return (
    <QueryState loading={loading} error={error} onRetry={reload}>
      <List
        dataSource={data ?? []}
        locale={{ emptyText: <Empty description="No comments yet" /> }}
        renderItem={(c) => (
          <List.Item>
            <List.Item.Meta
              title={`${c.user?.full_name ?? 'Unknown'} · ${formatDateTime(c.created_at)}`}
              description={<span style={{ whiteSpace: 'pre-wrap' }}>{c.body}</span>}
            />
          </List.Item>
        )}
      />
      <Input.TextArea
        rows={3}
        maxLength={2000}
        value={body}
        onChange={(e) => setBody(e.target.value)}
        placeholder="Write a comment"
        style={{ marginTop: 12 }}
      />
      <Button type="primary" loading={sending} onClick={send} style={{ marginTop: 8 }}>
        Add comment
      </Button>
    </QueryState>
  )
}

function Activity({ taskId }: { taskId: number }) {
  const fetcher = useCallback(() => tasksApi.activities(taskId), [taskId])
  const { data, loading, error, reload } = useFetch(fetcher)
  return (
    <QueryState loading={loading} error={error} onRetry={reload}>
      <Timeline
        items={(data ?? []).map((a) => ({
          content: (
            <>
              <div>{describe(a)}</div>
              <Typography.Text type="secondary">
                {formatDateTime(a.created_at)}
              </Typography.Text>
            </>
          ),
        }))}
      />
    </QueryState>
  )
}

export default function TaskDrawer({ task, onClose }: { task: Task | null; onClose: () => void }) {
  return (
    <Drawer open={!!task} onClose={onClose} title={task?.title} size="large" destroyOnHidden>
      {task && (
        <>
          <div style={{ marginBottom: 12 }}>
            <StatusTag value={task.status} /> <StatusTag value={task.priority} />
            {task.deadline && <span>Due {task.deadline}</span>}
          </div>
          <Typography.Paragraph>{task.description || 'No description'}</Typography.Paragraph>
          <Tabs
            items={[
              { key: 'c', label: 'Comments', children: <Comments taskId={task.id} /> },
              { key: 'a', label: 'Activity', children: <Activity taskId={task.id} /> },
            ]}
          />
        </>
      )}
    </Drawer>
  )
}
