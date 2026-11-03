import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Input, Select, Space, Table, Tag } from 'antd'
import { tasksApi } from '../api/tasks'
import { PageHeaderRow } from '../components/PageHeaderRow'
import TaskDrawer from '../components/TaskDrawer'
import TaskStatusSelect from '../components/TaskStatusSelect'
import { PRIORITIES, StatusTag, TASK_STATUSES, toOptions } from '../components/StatusTag'
import type { Page, Priority, Task, TaskStatus } from '../types'

export default function MyTasks() {
  const [data, setData] = useState<Page<Task> | null>(null)
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState<TaskStatus | undefined>()
  const [priority, setPriority] = useState<Priority | undefined>()
  const [page, setPage] = useState(1)
  const [drawerTask, setDrawerTask] = useState<Task | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      setData(
        await tasksApi.my({
          search: search || undefined,
          status,
          priority,
          page,
          size: 10,
          sort_by: 'deadline',
          order: 'asc',
        }),
      )
    } finally {
      setLoading(false)
    }
  }, [search, status, priority, page])

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load()
  }, [load])

  return (
    <>
      <PageHeaderRow title="My tasks" />
      <Space style={{ marginBottom: 16 }} wrap>
        <Input.Search
          placeholder="Search tasks"
          allowClear
          onSearch={(v) => {
            setSearch(v)
            setPage(1)
          }}
          style={{ width: 240 }}
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
            render: (t: string, task) => <a onClick={() => setDrawerTask(task)}>{t}</a>,
          },
          {
            title: 'Project',
            dataIndex: 'project_id',
            render: (id: number) => <Link to={`/projects/${id}`}>Open project</Link>,
          },
          {
            title: 'Status',
            render: (_, t) => <TaskStatusSelect task={t} onChanged={load} />,
          },
          {
            title: 'Priority',
            dataIndex: 'priority',
            render: (v: Priority) => <StatusTag value={v} />,
          },
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
        ]}
      />
      <TaskDrawer task={drawerTask} onClose={() => setDrawerTask(null)} />
    </>
  )
}
