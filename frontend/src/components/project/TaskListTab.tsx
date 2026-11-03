import { useCallback, useEffect, useState } from 'react'
import { Button, Popconfirm, Select, Space, Table, Tag } from 'antd'
import SearchInput from '../SearchInput'
import { DeleteOutlined } from '@ant-design/icons'
import { tasksApi, type TaskListParams } from '../../api/tasks'
import TaskStatusSelect from '../TaskStatusSelect'
import { StatusTag } from '../StatusTag'
import { PRIORITIES, TASK_STATUSES, toOptions } from '../../lib/options'
import type { Page, Priority, Task, TaskStatus } from '../../types'

export default function TaskListTab({
  projectId,
  canManage,
  meId,
  refreshKey,
  onOpen,
  onEdit,
  onChanged,
}: {
  projectId: number
  canManage: boolean
  meId: number
  refreshKey: number
  onOpen: (t: Task) => void
  onEdit: (t: Task) => void
  onChanged: () => void
}) {
  const [data, setData] = useState<Page<Task> | null>(null)
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState<TaskStatus | undefined>()
  const [priority, setPriority] = useState<Priority | undefined>()
  const [page, setPage] = useState(1)

  const load = useCallback(async () => {
    setLoading(true)
    const params: TaskListParams = {
      search: search || undefined,
      status,
      priority,
      page,
      size: 10,
      sort_by: 'created_at',
      order: 'desc',
    }
    try {
      setData(await tasksApi.listByProject(projectId, params))
    } finally {
      setLoading(false)
    }
  }, [projectId, search, status, priority, page])

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load()
  }, [load, refreshKey])

  const remove = async (id: number) => {
    try {
      await tasksApi.remove(id)
      onChanged()
    } catch {
      // error toast comes from the axios interceptor
    }
  }

  return (
    <>
      <Space style={{ marginBottom: 16 }} wrap>
        <SearchInput
          placeholder="Search tasks"
          onSearch={(v) => {
            setSearch(v)
            setPage(1)
          }}
        />
        <Select
          allowClear
          placeholder="Status"
          options={toOptions(TASK_STATUSES)}
          value={status}
          onChange={(v) => {
            setStatus(v)
            setPage(1)
          }}
          style={{ width: 150 }}
        />
        <Select
          allowClear
          placeholder="Priority"
          options={toOptions(PRIORITIES)}
          value={priority}
          onChange={(v) => {
            setPriority(v)
            setPage(1)
          }}
          style={{ width: 150 }}
        />
      </Space>
      <Table<Task>
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
          {
            title: 'Title',
            dataIndex: 'title',
            render: (t: string, task) => <a onClick={() => onOpen(task)}>{t}</a>,
          },
          {
            title: 'Status',
            render: (_, task) => (
              <TaskStatusSelect
                task={task}
                disabled={!canManage && task.assignee?.id !== meId}
                onChanged={onChanged}
              />
            ),
          },
          {
            title: 'Priority',
            dataIndex: 'priority',
            render: (v: Priority) => <StatusTag value={v} />,
          },
          { title: 'Assignee', render: (_, t) => t.assignee?.full_name ?? '-' },
          {
            title: 'Deadline',
            render: (_, t) => (
              <>
                {t.deadline ?? '-'}
                {t.is_overdue && <Tag color="red">Overdue</Tag>}
                {!t.is_overdue && t.due_soon && <Tag color="orange">Due soon</Tag>}
              </>
            ),
          },
          {
            title: '',
            render: (_, t) =>
              canManage && (
                <Space>
                  <Button size="small" onClick={() => onEdit(t)}>
                    Edit
                  </Button>
                  <Popconfirm title="Delete task?" onConfirm={() => remove(t.id)}>
                    <Button size="small" danger icon={<DeleteOutlined />} />
                  </Popconfirm>
                </Space>
              ),
          },
        ]}
      />
    </>
  )
}
