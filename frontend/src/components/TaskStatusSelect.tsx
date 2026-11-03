import { useState } from 'react'
import { Select, message } from 'antd'
import { tasksApi } from '../api/tasks'
import { TASK_STATUSES, toOptions } from './StatusTag'
import type { Task, TaskStatus } from '../types'

export default function TaskStatusSelect({
  task,
  disabled,
  onChanged,
}: {
  task: Task
  disabled?: boolean
  onChanged: () => void
}) {
  const [loading, setLoading] = useState(false)

  const change = async (status: TaskStatus) => {
    setLoading(true)
    try {
      await tasksApi.updateStatus(task.id, status)
      message.success('Status updated')
      onChanged()
    } catch {
      // error toast comes from the axios interceptor
    } finally {
      setLoading(false)
    }
  }

  return (
    <Select
      size="small"
      style={{ width: 130 }}
      value={task.status}
      options={toOptions(TASK_STATUSES)}
      disabled={disabled}
      loading={loading}
      onChange={change}
    />
  )
}
