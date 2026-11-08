import { useEffect, useState } from 'react'
import { Alert, Button, Descriptions, Form, Input, Modal, Space } from 'antd'
import { DeleteOutlined } from '@ant-design/icons'
import { tasksApi } from '../api'
import { StatusTag } from '../../../components/StatusTag'
import type { Task } from '../../../types'

const MIN_REASON = 3

// Confirmation popup for deleting a task: shows the task and requires a reason (saved in the project's activity).
export default function DeleteTaskModal({
  task,
  onClose,
  onDeleted,
}: {
  task: Task | null
  onClose: () => void
  onDeleted: () => void
}) {
  const [reason, setReason] = useState('')
  const [deleting, setDeleting] = useState(false)
  const [touched, setTouched] = useState(false)

  useEffect(() => {
    if (task) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setReason('')
      setTouched(false)
    }
  }, [task])

  const valid = reason.trim().length >= MIN_REASON

  const confirm = async () => {
    setTouched(true)
    if (!task || !valid) return
    setDeleting(true)
    try {
      await tasksApi.remove(task.id, reason.trim())
      onDeleted()
      onClose()
    } catch {
      // the axios interceptor already showed the error
    } finally {
      setDeleting(false)
    }
  }

  return (
    <Modal
      open={!!task}
      onCancel={onClose}
      centered
      destroyOnHidden
      title="Delete task"
      footer={
        <Space>
          <Button onClick={onClose}>Cancel</Button>
          <Button danger type="primary" icon={<DeleteOutlined />} loading={deleting} disabled={!valid} onClick={confirm}>
            Delete task
          </Button>
        </Space>
      }
    >
      {task && (
        <>
          <Alert
            type="warning"
            showIcon
            style={{ marginBottom: 16 }}
            title="This cannot be undone. The reason you enter is saved in the project activity."
          />
          <Descriptions column={1} size="small" bordered style={{ marginBottom: 16 }}>
            <Descriptions.Item label="Task">{task.title}</Descriptions.Item>
            <Descriptions.Item label="Project">{task.project_name ?? `#${task.project_id}`}</Descriptions.Item>
            <Descriptions.Item label="Status">
              <StatusTag value={task.status} />
            </Descriptions.Item>
            <Descriptions.Item label="Priority">
              <StatusTag value={task.priority} />
            </Descriptions.Item>
            <Descriptions.Item label="Assignee">{task.assignee?.full_name ?? 'Unassigned'}</Descriptions.Item>
            <Descriptions.Item label="Deadline">{task.deadline ?? '-'}</Descriptions.Item>
          </Descriptions>
          <Form layout="vertical" onFinish={confirm}>
            <Form.Item
              label="Reason for deleting (required)"
              validateStatus={touched && !valid ? 'error' : undefined}
              help={touched && !valid ? `Please enter at least ${MIN_REASON} characters` : undefined}
              required
            >
              <Input.TextArea
                rows={3}
                maxLength={500}
                showCount
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                placeholder="Why is this task being deleted?"
              />
            </Form.Item>
          </Form>
        </>
      )}
    </Modal>
  )
}
