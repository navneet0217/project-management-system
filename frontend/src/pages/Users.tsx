import { useCallback, useEffect, useState } from 'react'
import { Button, Form, Input, Modal, Select, Space, Switch, Table, Typography, message } from 'antd'
import { PlusOutlined } from '@ant-design/icons'
import { usersApi, type UserCreatePayload, type UserUpdatePayload } from '../api/users'
import { useAppSelector } from '../store'
import { PageHeaderRow } from '../components/PageHeaderRow'
import { ROLES, StatusTag, toOptions } from '../components/StatusTag'
import type { Page, Role, User } from '../types'

const PASSWORD_RULE = {
  min: 8,
  message: 'At least 8 characters',
}

export default function Users() {
  const me = useAppSelector((s) => s.auth.user)!
  const [data, setData] = useState<Page<User> | null>(null)
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [role, setRole] = useState<Role | undefined>()
  const [page, setPage] = useState(1)
  const [editing, setEditing] = useState<User | 'new' | null>(null)
  const [saving, setSaving] = useState(false)
  const [form] = Form.useForm()

  const load = useCallback(async () => {
    setLoading(true)
    try {
      setData(await usersApi.list({ search: search || undefined, role, page, size: 10 }))
    } finally {
      setLoading(false)
    }
  }, [search, role, page])

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load()
  }, [load])

  const openModal = (u: User | 'new') => {
    form.resetFields()
    if (u !== 'new') form.setFieldsValue(u)
    setEditing(u)
  }

  const submit = async (values: Record<string, unknown>) => {
    setSaving(true)
    try {
      if (editing === 'new') {
        await usersApi.create(values as unknown as UserCreatePayload)
        message.success('User created')
      } else if (editing) {
        const payload = { ...values } as UserUpdatePayload
        if (!payload.password) delete payload.password
        await usersApi.update(editing.id, payload)
        message.success('User updated')
      }
      setEditing(null)
      load()
    } catch {
      // the axios interceptor already showed the error
    } finally {
      setSaving(false)
    }
  }

  return (
    <>
      <PageHeaderRow
        title="Users"
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={() => openModal('new')}>
            New user
          </Button>
        }
      />
      <Space style={{ marginBottom: 16 }} wrap>
        <Input.Search
          placeholder="Search name or email"
          allowClear
          onSearch={(v) => {
            setSearch(v)
            setPage(1)
          }}
          style={{ width: 260 }}
        />
        <Select
          allowClear
          placeholder="Role"
          options={toOptions(ROLES)}
          value={role}
          onChange={(v) => {
            setRole(v)
            setPage(1)
          }}
          style={{ width: 160 }}
        />
      </Space>
      <Table<User>
        rowKey="id"
        loading={loading}
        dataSource={data?.items}
        scroll={{ x: 'max-content' }}
        pagination={{
          current: page,
          pageSize: 10,
          total: data?.total ?? 0,
          onChange: setPage,
          showSizeChanger: false,
        }}
        columns={[
          { title: 'Name', dataIndex: 'full_name' },
          { title: 'Email', dataIndex: 'email' },
          { title: 'Role', dataIndex: 'role', render: (r: Role) => <StatusTag value={r} /> },
          {
            title: 'Active',
            dataIndex: 'is_active',
            render: (v: boolean) => (v ? 'Yes' : 'No'),
          },
          {
            title: 'Created',
            dataIndex: 'created_at',
            render: (v: string) => new Date(v).toLocaleDateString(),
          },
          {
            title: '',
            render: (_, u) => (
              <Button size="small" onClick={() => openModal(u)}>
                Edit
              </Button>
            ),
          },
        ]}
      />

      <Modal
        open={!!editing}
        title={editing === 'new' ? 'New user' : 'Edit user'}
        onCancel={() => setEditing(null)}
        onOk={() => form.submit()}
        confirmLoading={saving}
        destroyOnHidden
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={submit}
          initialValues={{ role: 'DEVELOPER', is_active: true }}
        >
          {editing === 'new' && (
            <Form.Item
              name="email"
              label="Email"
              rules={[{ required: true, type: 'email', message: 'Enter a valid email' }]}
            >
              <Input />
            </Form.Item>
          )}
          <Form.Item
            name="full_name"
            label="Full name"
            rules={[{ required: true, min: 2, max: 120 }]}
          >
            <Input />
          </Form.Item>
          <Form.Item name="role" label="Role" rules={[{ required: true }]}>
            <Select
              options={toOptions(ROLES)}
              disabled={editing !== 'new' && editing?.id === me.id}
            />
          </Form.Item>
          {editing !== 'new' && (
            <Form.Item name="is_active" label="Active" valuePropName="checked">
              <Switch disabled={editing?.id === me.id} />
            </Form.Item>
          )}
          <Form.Item
            name="password"
            label={editing === 'new' ? 'Password' : 'New password (optional)'}
            rules={[{ required: editing === 'new' }, PASSWORD_RULE]}
            extra="Min 8 characters, with letters and numbers"
          >
            <Input.Password autoComplete="new-password" />
          </Form.Item>
        </Form>
      </Modal>
      <Typography.Text type="secondary">
        You cannot deactivate or demote your own account.
      </Typography.Text>
    </>
  )
}
