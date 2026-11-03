import { useCallback, useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  Button,
  Card,
  Descriptions,
  Input,
  List,
  Popconfirm,
  Progress,
  Select,
  Space,
  Table,
  Tag,
  Typography,
  message,
} from 'antd'
import { DeleteOutlined, PlusOutlined } from '@ant-design/icons'
import { projectsApi } from '../api/projects'
import { tasksApi, type TaskListParams } from '../api/tasks'
import { usersApi } from '../api/users'
import { useFetch } from '../hooks/useFetch'
import { useAppSelector } from '../store'
import QueryState from '../components/QueryState'
import ProjectFormModal from '../components/ProjectFormModal'
import TaskFormModal from '../components/TaskFormModal'
import TaskDrawer from '../components/TaskDrawer'
import TaskStatusSelect from '../components/TaskStatusSelect'
import { PRIORITIES, StatusTag, TASK_STATUSES, toOptions } from '../components/StatusTag'
import type { Page, Priority, Task, TaskStatus, UserOption } from '../types'

export default function ProjectDetail() {
  const projectId = Number(useParams().id)
  const navigate = useNavigate()
  const me = useAppSelector((s) => s.auth.user)!

  const projectFetcher = useCallback(() => projectsApi.get(projectId), [projectId])
  const membersFetcher = useCallback(() => projectsApi.members(projectId), [projectId])
  const project = useFetch(projectFetcher)
  const members = useFetch(membersFetcher)

  const [tasks, setTasks] = useState<Page<Task> | null>(null)
  const [tasksLoading, setTasksLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState<TaskStatus | undefined>()
  const [priority, setPriority] = useState<Priority | undefined>()
  const [page, setPage] = useState(1)

  const [editingProject, setEditingProject] = useState(false)
  const [taskModal, setTaskModal] = useState<{ open: boolean; task: Task | null }>({
    open: false,
    task: null,
  })
  const [drawerTask, setDrawerTask] = useState<Task | null>(null)
  const [candidates, setCandidates] = useState<UserOption[]>([])
  const [newMember, setNewMember] = useState<number | undefined>()

  const canManage =
    !!project.data && (me.role === 'ADMIN' || project.data.manager?.id === me.id)

  const loadTasks = useCallback(async () => {
    setTasksLoading(true)
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
      setTasks(await tasksApi.listByProject(projectId, params))
    } finally {
      setTasksLoading(false)
    }
  }, [projectId, search, status, priority, page])

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadTasks()
  }, [loadTasks])

  useEffect(() => {
    if (canManage) usersApi.options('DEVELOPER').then(setCandidates).catch(() => {})
  }, [canManage])

  const refreshAll = () => {
    project.reload()
    members.reload()
    loadTasks()
  }

  const memberIds = new Set((members.data ?? []).map((m) => m.id))
  const addable = candidates.filter((c) => !memberIds.has(c.id))

  const addMember = async () => {
    if (!newMember) return
    try {
      await projectsApi.addMember(projectId, newMember)
      setNewMember(undefined)
      refreshAll()
    } catch {
      // error toast comes from the axios interceptor
    }
  }

  const removeMember = async (id: number) => {
    try {
      await projectsApi.removeMember(projectId, id)
      refreshAll()
    } catch {
      // error toast comes from the axios interceptor
    }
  }

  const deleteProject = async () => {
    try {
      await projectsApi.remove(projectId)
      message.success('Project deleted')
      navigate('/projects')
    } catch {
      // error toast comes from the axios interceptor
    }
  }

  const deleteTask = async (id: number) => {
    try {
      await tasksApi.remove(id)
      loadTasks()
      project.reload()
    } catch {
      // error toast comes from the axios interceptor
    }
  }

  const p = project.data

  return (
    <QueryState loading={project.loading && !p} error={project.error} onRetry={project.reload}>
      {p && (
        <>
          <Space style={{ width: '100%', justifyContent: 'space-between' }} wrap>
            <Typography.Title level={3} style={{ margin: 0 }}>
              {p.name} <StatusTag value={p.status} />
            </Typography.Title>
            {canManage && (
              <Space>
                <Button onClick={() => setEditingProject(true)}>Edit</Button>
                <Popconfirm
                  title="Delete this project?"
                  description="Projects with open tasks cannot be deleted."
                  onConfirm={deleteProject}
                >
                  <Button danger icon={<DeleteOutlined />}>
                    Delete
                  </Button>
                </Popconfirm>
              </Space>
            )}
          </Space>

          <Card style={{ margin: '16px 0' }}>
            <Descriptions column={{ xs: 1, md: 2 }}>
              <Descriptions.Item label="Description">{p.description || '-'}</Descriptions.Item>
              <Descriptions.Item label="Manager">{p.manager?.full_name ?? '-'}</Descriptions.Item>
              <Descriptions.Item label="Dates">
                {p.start_date ?? '?'} → {p.end_date ?? '?'}
              </Descriptions.Item>
              <Descriptions.Item label="Progress">
                <Progress
                  percent={Math.round(p.completion_percentage)}
                  size="small"
                  format={() => `${p.done_tasks}/${p.total_tasks}`}
                />
              </Descriptions.Item>
            </Descriptions>
          </Card>

          <Card title={`Members (${members.data?.length ?? 0})`} style={{ marginBottom: 16 }}>
            {canManage && (
              <Space style={{ marginBottom: 12 }}>
                <Select
                  showSearch
                  optionFilterProp="label"
                  placeholder="Add a developer"
                  style={{ width: 240 }}
                  value={newMember}
                  onChange={setNewMember}
                  options={addable.map((u) => ({ value: u.id, label: u.full_name }))}
                />
                <Button type="primary" disabled={!newMember} onClick={addMember}>
                  Add
                </Button>
              </Space>
            )}
            <List
              dataSource={members.data ?? []}
              locale={{ emptyText: 'No members yet' }}
              renderItem={(m) => (
                <List.Item
                  actions={
                    canManage
                      ? [
                          <Popconfirm
                            key="rm"
                            title="Remove member? Their tasks here become unassigned."
                            onConfirm={() => removeMember(m.id)}
                          >
                            <Button size="small" danger>
                              Remove
                            </Button>
                          </Popconfirm>,
                        ]
                      : undefined
                  }
                >
                  {m.full_name} <Tag>{m.role}</Tag>
                </List.Item>
              )}
            />
          </Card>

          <Card
            title="Tasks"
            extra={
              canManage && (
                <Button
                  type="primary"
                  icon={<PlusOutlined />}
                  onClick={() => setTaskModal({ open: true, task: null })}
                >
                  New task
                </Button>
              )
            }
          >
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
              loading={tasksLoading}
              dataSource={tasks?.items}
              scroll={{ x: 'max-content' }}
              pagination={{
                current: page,
                pageSize: 10,
                total: tasks?.total ?? 0,
                onChange: setPage,
                showSizeChanger: false,
              }}
              columns={[
                {
                  title: 'Title',
                  dataIndex: 'title',
                  render: (t: string, task) => (
                    <a onClick={() => setDrawerTask(task)}>{t}</a>
                  ),
                },
                {
                  title: 'Status',
                  render: (_, task) => (
                    <TaskStatusSelect
                      task={task}
                      disabled={!canManage && task.assignee?.id !== me.id}
                      onChanged={() => {
                        loadTasks()
                        project.reload()
                      }}
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
                        <Button size="small" onClick={() => setTaskModal({ open: true, task: t })}>
                          Edit
                        </Button>
                        <Popconfirm title="Delete task?" onConfirm={() => deleteTask(t.id)}>
                          <Button size="small" danger icon={<DeleteOutlined />} />
                        </Popconfirm>
                      </Space>
                    ),
                },
              ]}
            />
          </Card>

          <ProjectFormModal
            open={editingProject}
            project={p}
            onClose={() => setEditingProject(false)}
            onSaved={project.reload}
          />
          <TaskFormModal
            open={taskModal.open}
            projectId={projectId}
            task={taskModal.task}
            members={members.data ?? []}
            onClose={() => setTaskModal({ open: false, task: null })}
            onSaved={() => {
              loadTasks()
              project.reload()
            }}
          />
          <TaskDrawer task={drawerTask} onClose={() => setDrawerTask(null)} />
        </>
      )}
    </QueryState>
  )
}
