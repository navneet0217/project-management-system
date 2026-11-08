import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Select, Space, Table, Tag } from 'antd'
import { type TaskListParams } from '../api'
import { useSort } from '../../../hooks/useSort'
import { formatDate } from '../../../lib/dates'
import SearchInput from '../../../components/SearchInput'
import { StatusTag } from '../../../components/StatusTag'
import TaskDrawer from './TaskDrawer'
import TaskStatusSelect from './TaskStatusSelect'
import { PRIORITIES, TASK_STATUSES, toOptions } from '../../../lib/options'
import { TASK_SORT_FIELDS, type TaskSort } from '../../../lib/taskParams'
import type { Page, Priority, Task, TaskStatus } from '../../../types'

const DEFAULT_SORT: TaskSort = { field: 'created_at', order: 'desc' }

// Sortable, filterable, paginated task table. The caller decides where the data comes from.
export default function TasksTable({
  fetcher,
  initial,
  refreshKey = 0,
  editableStatus = false,
  toolbar,
  actions,
}: {
  fetcher: (params: TaskListParams) => Promise<Page<Task>>
  initial?: { sort?: TaskSort; status?: TaskStatus; priority?: Priority }
  refreshKey?: number
  editableStatus?: boolean // show a status dropdown (for tasks the viewer may update)
  toolbar?: React.ReactNode
  actions?: (task: Task, reload: () => void) => React.ReactNode
}) {
  const { sort, sortProps, onTableChange } = useSort(TASK_SORT_FIELDS, initial?.sort ?? DEFAULT_SORT)
  const [data, setData] = useState<Page<Task> | null>(null)
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState<TaskStatus | undefined>(initial?.status)
  const [priority, setPriority] = useState<Priority | undefined>(initial?.priority)
  const [page, setPage] = useState(1)
  const [drawerTask, setDrawerTask] = useState<Task | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      setData(
        await fetcher({
          search: search || undefined,
          status,
          priority,
          sort_by: sort.field,
          order: sort.order,
          page,
          size: 10,
        }),
      )
    } finally {
      setLoading(false)
    }
  }, [fetcher, search, status, priority, sort, page])

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load()
  }, [load, refreshKey])

  return (
    <>
      <Space style={{ marginBottom: 16, width: '100%', justifyContent: 'space-between' }} wrap>
        <Space wrap>
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
        {toolbar}
      </Space>
      <Table<Task>
        rowKey="id"
        loading={loading}
        dataSource={data?.items}
        scroll={{ x: 'max-content' }}
        showSorterTooltip={false}
        locale={{ emptyText: 'No tasks found' }}
        pagination={{ current: page, pageSize: 10, total: data?.total ?? 0, showSizeChanger: false }}
        onChange={(pagination, _filters, sorter) => {
          onTableChange(sorter as never)
          setPage(pagination.current ?? 1)
        }}
        columns={[
          {
            title: 'Title',
            dataIndex: 'title',
            ...sortProps('title'),
            render: (t: string, task) => <a onClick={() => setDrawerTask(task)}>{t}</a>,
          },
          {
            title: 'Project',
            dataIndex: 'project_name',
            render: (name: string | null | undefined, t) => (
              <Link to={`/projects/${t.project_id}`}>{name ?? 'Open project'}</Link>
            ),
          },
          {
            title: 'Status',
            dataIndex: 'status',
            ...sortProps('status'),
            render: (v: TaskStatus, t) =>
              editableStatus ? <TaskStatusSelect task={t} onChanged={load} /> : <StatusTag value={v} />,
          },
          {
            title: 'Priority',
            dataIndex: 'priority',
            ...sortProps('priority'),
            render: (v: Priority) => <StatusTag value={v} />,
          },
          { title: 'Assignee', render: (_, t) => t.assignee?.full_name ?? '-' },
          {
            title: 'Deadline',
            dataIndex: 'deadline',
            ...sortProps('deadline'),
            render: (_, t) => (
              <>
                {t.deadline ?? '-'}
                {t.is_overdue && <Tag color="red">Overdue</Tag>}
                {!t.is_overdue && t.due_soon && <Tag color="orange">Due soon</Tag>}
              </>
            ),
          },
          {
            title: 'Created',
            dataIndex: 'created_at',
            ...sortProps('created_at'),
            render: (v: string) => formatDate(v),
          },
          ...(actions
            ? [
                {
                  title: 'Actions',
                  key: 'actions',
                  render: (_: unknown, t: Task) => (
                    <Space size="small">
                      <a onClick={() => setDrawerTask(t)}>View</a>
                      {actions(t, load)}
                    </Space>
                  ),
                },
              ]
            : []),
        ]}
      />
      <TaskDrawer task={drawerTask} onClose={() => setDrawerTask(null)} />
    </>
  )
}
