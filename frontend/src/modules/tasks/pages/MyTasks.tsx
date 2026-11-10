import { useCallback, useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Button, Tooltip } from 'antd'
import { DeleteOutlined, EditOutlined, PlusOutlined } from '@ant-design/icons'
import { taskTableInitial } from '../../../lib/taskParams'
import { hasRole } from '../../../lib/options'
import { projectsApi } from '../../projects/api'
import { tasksApi } from '../api'
import { PageHeaderRow } from '../../../components/PageHeaderRow'
import DeleteTaskModal from '../components/DeleteTaskModal'
import TaskFormModal from '../components/TaskFormModal'
import TasksTable from '../components/TasksTable'
import { useAppSelector } from '../../../store'
import type { Project, Task } from '../../../types'

const fetcher = tasksApi.my

// Tasks assigned to me. Developers can add, edit and delete their own tasks here.
export default function MyTasks() {
  const me = useAppSelector((s) => s.auth.user)!
  const [params] = useSearchParams()
  const isDeveloper = hasRole(me, 'DEVELOPER')
  const [version, setVersion] = useState(0)
  const [projects, setProjects] = useState<Project[]>([])
  const [form, setForm] = useState<{ open: boolean; task: Task | null }>({ open: false, task: null })
  const [deleting, setDeleting] = useState<Task | null>(null)
  const refresh = useCallback(() => setVersion((v) => v + 1), [])

  useEffect(() => {
    // for a developer this is exactly the projects they belong to
    if (isDeveloper) projectsApi.list({ size: 100, member_only: true }).then((p) => setProjects(p.items)).catch(() => {})
  }, [isDeveloper])

  return (
    <>
      <PageHeaderRow
        title="My tasks"
        extra={
          isDeveloper && (
            <Button type="primary" icon={<PlusOutlined />} onClick={() => setForm({ open: true, task: null })}>
              Add task
            </Button>
          )
        }
      />
      <TasksTable
        fetcher={fetcher}
        refreshKey={version}
        editableStatus
        initial={taskTableInitial(params, { field: 'deadline', order: 'asc' })}
        actions={(task) =>
          isDeveloper && (
            <>
              <Tooltip title="Edit task">
                <Button aria-label="Edit task" icon={<EditOutlined />} onClick={() => setForm({ open: true, task })} />
              </Tooltip>
              {/* a developer may only delete tasks they created themselves; the server enforces this too */}
              {task.created_by === me.id && (
                <Tooltip title="Delete task">
                  <Button aria-label="Delete task" danger icon={<DeleteOutlined />} onClick={() => setDeleting(task)} />
                </Tooltip>
              )}
            </>
          )
        }
      />
      <TaskFormModal
        mode="self"
        open={form.open}
        task={form.task}
        projects={projects}
        onClose={() => setForm({ open: false, task: null })}
        onSaved={refresh}
      />
      <DeleteTaskModal task={deleting} onClose={() => setDeleting(null)} onDeleted={refresh} />
    </>
  )
}
