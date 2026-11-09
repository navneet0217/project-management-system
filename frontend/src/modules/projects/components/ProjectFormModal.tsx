import { useEffect, useState } from 'react'
import { DatePicker, Form, Input, Modal, Select } from 'antd'
import dayjs, { type Dayjs } from 'dayjs'
import { projectsApi } from '../api'
import { usersApi } from '../../users/api'
import { useAppSelector } from '../../../store'
import { hasRole, PROJECT_STATUSES, toOptions } from '../../../lib/options'
import type { Project, ProjectPayload, ProjectStatus, UserOption } from '../../../types'

interface FormValues {
  name: string
  description?: string
  status: ProjectStatus
  dates?: [Dayjs | null, Dayjs | null]
  manager_id?: number
}

const fmt = (d?: Dayjs | null) => (d ? d.format('YYYY-MM-DD') : null)

export default function ProjectFormModal({
  open,
  project,
  onClose,
  onSaved,
}: {
  open: boolean
  project: Project | null
  onClose: () => void
  onSaved: () => void
}) {
  const me = useAppSelector((s) => s.auth.user)!
  const isAdmin = hasRole(me, 'ADMIN')
  const [form] = Form.useForm<FormValues>()
  const [saving, setSaving] = useState(false)
  const [managers, setManagers] = useState<UserOption[]>([])

  useEffect(() => {
    if (open && isAdmin) usersApi.options('MANAGER').then(setManagers).catch(() => {})
  }, [open, isAdmin])

  useEffect(() => {
    if (!open) return
    form.resetFields()
    if (project) {
      form.setFieldsValue({
        name: project.name,
        description: project.description ?? undefined,
        status: project.status,
        manager_id: project.manager?.id,
        dates: [
          project.start_date ? dayjs(project.start_date) : null,
          project.end_date ? dayjs(project.end_date) : null,
        ],
      })
    }
  }, [open, project, form])

  const submit = async (v: FormValues) => {
    const payload: ProjectPayload = {
      name: v.name,
      description: v.description || null,
      status: v.status,
      start_date: fmt(v.dates?.[0]),
      end_date: fmt(v.dates?.[1]),
    }
    if (isAdmin && v.manager_id) payload.manager_id = v.manager_id
    setSaving(true)
    try {
      if (project) await projectsApi.update(project.id, payload)
      else await projectsApi.create(payload)
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
      title={project ? 'Edit project' : 'New project'}
      onCancel={onClose}
      onOk={() => form.submit()}
      confirmLoading={saving}
      destroyOnHidden
    >
      <Form form={form} layout="vertical" onFinish={submit} initialValues={{ status: 'PLANNING' }}>
        <Form.Item name="name" label="Name" rules={[{ required: true, min: 3, max: 150 }]}>
          <Input />
        </Form.Item>
        <Form.Item name="description" label="Description" rules={[{ max: 5000 }]}>
          <Input.TextArea rows={3} />
        </Form.Item>
        <Form.Item name="status" label="Status">
          <Select options={toOptions(PROJECT_STATUSES)} />
        </Form.Item>
        <Form.Item name="dates" label="Start / end date">
          <DatePicker.RangePicker style={{ width: '100%' }} allowEmpty={[true, true]} />
        </Form.Item>
        {isAdmin && (
          <Form.Item name="manager_id" label="Manager">
            <Select
              allowClear
              placeholder="Defaults to you"
              options={managers.map((m) => ({ value: m.id, label: m.full_name }))}
            />
          </Form.Item>
        )}
      </Form>
    </Modal>
  )
}
