import { useEffect, useState } from 'react'
import { DatePicker, Form, Input, Modal, Select } from 'antd'
import dayjs from 'dayjs'
import { tasksApi } from '../api/tasks'
import { PRIORITIES, toOptions } from '../lib/options'
import type { Priority, Task, UserOption } from '../types'

interface FormValues {
  title: string
  description?: string
  priority: Priority
  deadline?: dayjs.Dayjs | null
  assignee_id?: number | null
}

export default function TaskFormModal({
  open,
  projectId,
  task,
  members,
  onClose,
  onSaved,
}: {
  open: boolean
  projectId: number
  task: Task | null
  members: UserOption[]
  onClose: () => void
  onSaved: () => void
}) {
  const [form] = Form.useForm<FormValues>()
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (!open) return
    form.resetFields()
    if (task) {
      form.setFieldsValue({
        title: task.title,
        description: task.description ?? undefined,
        priority: task.priority,
        deadline: task.deadline ? dayjs(task.deadline) : null,
        assignee_id: task.assignee?.id ?? null,
      })
    }
  }, [open, task, form])

  const submit = async (v: FormValues) => {
    const payload = {
      title: v.title,
      description: v.description || null,
      priority: v.priority,
      deadline: v.deadline ? v.deadline.format('YYYY-MM-DD') : null,
      assignee_id: v.assignee_id ?? null,
    }
    setSaving(true)
    try {
      if (task) await tasksApi.update(task.id, payload)
      else await tasksApi.create(projectId, payload)
      onSaved()
      onClose()
    } catch {
      // error toast comes from the axios interceptor
    } finally {
      setSaving(false)
    }
  }

  return (
    <Modal
      open={open}
      title={task ? 'Edit task' : 'New task'}
      onCancel={onClose}
      onOk={() => form.submit()}
      confirmLoading={saving}
      destroyOnHidden
    >
      <Form form={form} layout="vertical" onFinish={submit} initialValues={{ priority: 'MEDIUM' }}>
        <Form.Item name="title" label="Title" rules={[{ required: true, min: 3, max: 200 }]}>
          <Input />
        </Form.Item>
        <Form.Item name="description" label="Description" rules={[{ max: 5000 }]}>
          <Input.TextArea rows={3} />
        </Form.Item>
        <Form.Item name="priority" label="Priority">
          <Select options={toOptions(PRIORITIES)} />
        </Form.Item>
        <Form.Item name="deadline" label="Deadline">
          <DatePicker style={{ width: '100%' }} />
        </Form.Item>
        <Form.Item name="assignee_id" label="Assignee">
          <Select
            allowClear
            placeholder="Unassigned"
            options={members.map((m) => ({ value: m.id, label: m.full_name }))}
          />
        </Form.Item>
      </Form>
    </Modal>
  )
}
