import { useCallback, useEffect, useState } from 'react'
import { App, Button, Form, Input, Modal, Segmented, Select, Space, Switch, Table, Tag, Typography } from 'antd'
import { DeleteOutlined, EyeOutlined, PlusOutlined, UndoOutlined } from '@ant-design/icons'
import { Link } from 'react-router-dom'
import SearchInput from '../../../components/SearchInput'
import UserProfileModal from '../components/UserProfileModal'
import {
  usersApi,
  type UserCreatePayload,
  type UserSortField,
  type UserUpdatePayload,
} from '../api'
import { useSort } from '../../../hooks/useSort'
import { formatDate } from '../../../lib/dates'
import { useAppSelector } from '../../../store'
import { PageHeaderRow } from '../../../components/PageHeaderRow'
import { StatusTag } from '../../../components/StatusTag'
import { ROLES, toOptions } from '../../../lib/options'
import type { Page, ProjectRef, Role, UserListItem, UserOption } from '../../../types'

const PASSWORD_RULE = {
  min: 8,
  message: 'At least 8 characters',
}

const SORT_FIELDS: readonly UserSortField[] = ['full_name', 'email', 'role', 'is_active', 'created_at']
const DEFAULT_SORT = { field: 'created_at', order: 'desc' } as const

export default function Users() {
  const { message, modal } = App.useApp()
  const me = useAppSelector((s) => s.auth.user)!
  const { sort, sortProps, onTableChange } = useSort<UserSortField>(SORT_FIELDS, DEFAULT_SORT)
  const [data, setData] = useState<Page<UserListItem> | null>(null)
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [role, setRole] = useState<Role | undefined>()
  const [view, setView] = useState<'users' | 'removed'>('users')
  const [page, setPage] = useState(1)
  const [editing, setEditing] = useState<UserListItem | 'new' | null>(null)
  const [saving, setSaving] = useState(false)
  const [profileId, setProfileId] = useState<number | null>(null)
  const [togglingId, setTogglingId] = useState<number | null>(null)
  const [form] = Form.useForm()

  const load = useCallback(async () => {
    setLoading(true)
    try {
      setData(
        await usersApi.list({
          search: search || undefined,
          role,
          removed: view === 'removed',
          sort_by: sort.field,
          order: sort.order,
          page,
          size: 10,
        }),
      )
    } finally {
      setLoading(false)
    }
  }, [search, role, view, sort, page])

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load()
  }, [load])

  const openModal = (u: UserListItem | 'new') => {
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

  const setActive = async (u: UserListItem, active: boolean) => {
    setTogglingId(u.id)
    try {
      await usersApi.update(u.id, { is_active: active })
      message.success(`${u.full_name} is now ${active ? 'active' : 'inactive'}`)
      load()
    } catch {
      // the axios interceptor already showed the error
    } finally {
      setTogglingId(null)
    }
  }

  const toggle = (u: UserListItem, active: boolean) => {
    if (active) return setActive(u, true)
    modal.confirm({
      title: `Deactivate ${u.full_name}?`,
      content: 'They will be signed out and will not be able to log in until you activate them again.',
      okText: 'Deactivate',
      okButtonProps: { danger: true },
      centered: true,
      onOk: () => setActive(u, false),
    })
  }

  const removeUser = (u: UserListItem) =>
    modal.confirm({
      title: `Remove ${u.full_name}?`,
      content:
        'They will be hidden from the user list and signed out. Their tasks and activity history are kept, and you can restore them later from the Removed view.',
      okText: 'Remove',
      okButtonProps: { danger: true },
      centered: true,
      onOk: async () => {
        try {
          await usersApi.remove(u.id)
          message.success(`${u.full_name} was removed`)
          load()
        } catch {
          // the axios interceptor already showed the error (for example: still manages an active project)
        }
      },
    })

  const restoreUser = async (u: UserListItem) => {
    try {
      await usersApi.restore(u.id)
      message.success(`${u.full_name} was restored (inactive until you activate them)`)
      load()
    } catch {
      // the axios interceptor already showed the error
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
        <Segmented
          value={view}
          onChange={(v) => {
            setView(v as 'users' | 'removed')
            setPage(1)
          }}
          options={[
            { value: 'users', label: 'Users' },
            { value: 'removed', label: 'Removed' },
          ]}
        />
        <SearchInput
          placeholder="Search name or email"
          onSearch={(v) => {
            setSearch(v)
            setPage(1)
          }}
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
      <Table<UserListItem>
        rowKey="id"
        loading={loading}
        dataSource={data?.items}
        scroll={{ x: 'max-content' }}
        showSorterTooltip={false}
        pagination={{ current: page, pageSize: 10, total: data?.total ?? 0, showSizeChanger: false }}
        onChange={(pagination, _filters, sorter) => {
          onTableChange(sorter as never)
          setPage(pagination.current ?? 1)
        }}
        columns={[
          { title: 'Name', dataIndex: 'full_name', ...sortProps('full_name') },
          { title: 'Email', dataIndex: 'email', ...sortProps('email') },
          {
            title: 'Role',
            dataIndex: 'role',
            ...sortProps('role'),
            render: (r: Role) => <StatusTag value={r} />,
          },
          {
            title: 'Status',
            dataIndex: 'is_active',
            ...sortProps('is_active'),
            render: (v: boolean) => <Tag color={v ? 'success' : 'default'}>{v ? 'Active' : 'Inactive'}</Tag>,
          },
          {
            title: 'Projects',
            dataIndex: 'projects',
            render: (projects: ProjectRef[]) =>
              projects.length ? (
                <div className="chip-row">
                  {projects.map((p) => (
                    <Tag key={p.id} color="teal">
                      <Link to={`/projects/${p.id}`}>{p.name}</Link>
                    </Tag>
                  ))}
                </div>
              ) : (
                <Typography.Text type="secondary">-</Typography.Text>
              ),
          },
          {
            title: 'Manager',
            dataIndex: 'managers',
            render: (managers: UserOption[]) =>
              managers.length ? (
                <div className="chip-row">
                  {managers.map((m) => (
                    <Tag key={m.id}>{m.full_name}</Tag>
                  ))}
                </div>
              ) : (
                <Typography.Text type="secondary">-</Typography.Text>
              ),
          },
          {
            title: 'Created',
            dataIndex: 'created_at',
            ...sortProps('created_at'),
            render: (v: string) => formatDate(v),
          },
          {
            title: 'Actions',
            key: 'actions',
            fixed: 'right',
            render: (_, u) =>
              u.deleted_at ? (
                <Space size="small" wrap>
                  <Button size="small" icon={<EyeOutlined />} onClick={() => setProfileId(u.id)}>
                    View profile
                  </Button>
                  <Button size="small" type="primary" ghost icon={<UndoOutlined />} onClick={() => restoreUser(u)}>
                    Restore
                  </Button>
                </Space>
              ) : (
                <Space size="small" wrap>
                  <Button size="small" onClick={() => openModal(u)}>
                    Edit
                  </Button>
                  <Switch
                    size="small"
                    checked={u.is_active}
                    loading={togglingId === u.id}
                    disabled={u.id === me.id}
                    checkedChildren="Active"
                    unCheckedChildren="Inactive"
                    onChange={(checked) => toggle(u, checked)}
                    title={u.id === me.id ? 'You cannot deactivate your own account' : undefined}
                  />
                  <Button size="small" icon={<EyeOutlined />} onClick={() => setProfileId(u.id)}>
                    View profile
                  </Button>
                  {u.id !== me.id && (
                    <Button size="small" danger icon={<DeleteOutlined />} onClick={() => removeUser(u)}>
                      Remove
                    </Button>
                  )}
                </Space>
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
        centered
        destroyOnHidden
      >
        <Form form={form} layout="vertical" onFinish={submit} initialValues={{ role: 'DEVELOPER' }}>
          {editing === 'new' && (
            <Form.Item
              name="email"
              label="Email"
              rules={[{ required: true, type: 'email', message: 'Enter a valid email' }]}
            >
              <Input />
            </Form.Item>
          )}
          <Form.Item name="full_name" label="Full name" rules={[{ required: true, min: 2, max: 120 }]}>
            <Input />
          </Form.Item>
          <Form.Item name="role" label="Role" rules={[{ required: true }]}>
            <Select
              options={toOptions(ROLES)}
              disabled={editing !== 'new' && editing?.id === me.id}
            />
          </Form.Item>
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

      <UserProfileModal userId={profileId} onClose={() => setProfileId(null)} />

      <Typography.Text type="secondary">
        You cannot deactivate or demote your own account. Project allocation is managed on each project's members list.
      </Typography.Text>
    </>
  )
}
