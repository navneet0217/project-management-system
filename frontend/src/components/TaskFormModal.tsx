import { useEffect, useState } from 'react'
import { DatePicker, Form, Input, Modal, Select } from 'antd'
import dayjs from 'dayjs'
import { tasksApi } from '../api/tasks'
import { PRIORITIES, toOptions } from '../lib/options'
import type { Priority, Project, Task, UserOption } from '../types'

interface FormValues {
  project_id?: number
  title: string
  description?: string
  priority: Priority
  deadline?: dayjs.Dayjs | null
  assignee_id?: number | null
}

// One form for two situations:
// - manager/admin ("manage"): project is fixed, pick any member as assignee
// - developer ("self"): the task is always for the developer; when creating, pick one of their projects
export default function TaskFormModal({
  open,
  projectId,
  task,
  members = [],
  projects,
  mode = 'manage',
  onClose,
  onSaved,
}: {
  open: boolean
  projectId?: number
  task: Task | null
  members?: UserOption[]
  projects?: Project[]
  mode?: 'manage' | 'self'
  onClose: () => void
  onSaved: () => void
}) {
  const [form] = Form.useForm<FormValues>()
  const [saving, setSaving] = useState(false)
  const self = mode === 'self'
  const pickProject = self && !task

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
    const base = {
      title: v.title,
      description: v.description || null,
      priority: v.priority,
      deadline: v.deadline ? v.deadline.format('YYYY-MM-DD') : null,
    }
    setSaving(true)
    try {
      if (task) {
        // developers cannot change the assignee, so do not send it
        await tasksApi.update(task.id, self ? base : { ...base, assignee_id: v.assignee_id ?? null })
      } else {
        const target = pickProject ? v.project_id! : projectId!
        await tasksApi.create(target, self ? base : { ...base, assignee_id: v.assignee_id ?? null })
      }
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
      title={task ? 'Edit task' : self ? 'Add my task' : 'New task'}
      onCancel={onClose}
      onOk={() => form.submit()}
      confirmLoading={saving}
      centered
      destroyOnHidden
    >
      <Form form={form} layout="vertical" onFinish={submit} initialValues={{ priority: 'MEDIUM' }}>
        {pickProject && (
          <Form.Item name="project_id" label="Project" rules={[{ required: true, message: 'Choose a project' }]}>
            <Select
              showSearch
              optionFilterProp="label"
              placeholder="Choose one of your projects"
              options={(projects ?? []).map((p) => ({ value: p.id, label: p.name }))}
              notFoundContent="You are not a member of any project yet"
            />
          </Form.Item>
        )}
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
        {!self && (
          <Form.Item name="assignee_id" label="Assignee">
            <Select
              allowClear
              placeholder="Unassigned"
              options={members.map((m) => ({ value: m.id, label: m.full_name }))}
            />
          </Form.Item>
        )}
      </Form>
    </Modal>
  )
}
