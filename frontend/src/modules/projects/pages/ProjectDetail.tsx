import { useCallback, useState } from 'react'
import { useParams } from 'react-router-dom'
import { Button, Card, Col, Row, Tabs } from 'antd'
import { AppstoreOutlined, HistoryOutlined, PlusOutlined, UnorderedListOutlined } from '@ant-design/icons'
import { projectsApi } from '../api'
import { useFetch } from '../../../hooks/useFetch'
import { useAppSelector } from '../../../store'
import QueryState from '../../../components/QueryState'
import KanbanBoard from '../../tasks/components/KanbanBoard'
import MembersCard from '../components/MembersCard'
import ProjectSummary from '../components/ProjectSummary'
import ActivityTab from '../components/ActivityTab'
import TaskListTab from '../components/TaskListTab'
import TaskDrawer from '../../tasks/components/TaskDrawer'
import TaskFormModal from '../../tasks/components/TaskFormModal'
import type { Task } from '../../../types'
import { hasRole } from '../../../lib/options'

export default function ProjectDetail() {
  const projectId = Number(useParams().id)
  const me = useAppSelector((s) => s.auth.user)!

  const projectFetcher = useCallback(() => projectsApi.get(projectId), [projectId])
  const membersFetcher = useCallback(() => projectsApi.members(projectId), [projectId])
  const project = useFetch(projectFetcher)
  const members = useFetch(membersFetcher)

  // Bumped after any change so the board and the list both reload.
  const [version, setVersion] = useState(0)
  const [taskModal, setTaskModal] = useState<{ open: boolean; task: Task | null }>({
    open: false,
    task: null,
  })
  const [drawerTask, setDrawerTask] = useState<Task | null>(null)

  const p = project.data
  const canManage = !!p && (hasRole(me, 'ADMIN') || (hasRole(me, 'MANAGER') && p.manager?.id === me.id))
  const canCreateTask = canManage || (hasRole(me, 'DEVELOPER') && !!members.data?.some((member) => member.id === me.id))
  const canMove = (t: Task) => canManage || t.assignee?.id === me.id

  const refresh = () => {
    project.reload()
    setVersion((v) => v + 1)
  }
  const refreshAll = () => {
    members.reload()
    refresh()
  }

  return (
    <QueryState loading={project.loading && !p} error={project.error} onRetry={project.reload}>
      {p && (
        <>
          <ProjectSummary project={p} canManage={canManage} onChanged={refresh} />

          <Row gutter={[20, 20]}>
            <Col xs={24}>
              <Card
                className="soft-card"
                extra={
                  canCreateTask && (
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
                {/* destroyOnHidden: each tab reloads when opened, so Activity always shows the latest entries */}
                <Tabs
                  destroyOnHidden
                  items={[
                    {
                      key: 'board',
                      label: (
                        <span>
                          <AppstoreOutlined /> Board
                        </span>
                      ),
                      children: (
                        <KanbanBoard
                          projectId={projectId}
                          canMove={canMove}
                          onOpen={setDrawerTask}
                          onChanged={project.reload}
                          refreshKey={version}
                        />
                      ),
                    },
                    {
                      key: 'list',
                      label: (
                        <span>
                          <UnorderedListOutlined /> List
                        </span>
                      ),
                      children: (
                        <TaskListTab
                          projectId={projectId}
                          canManage={canManage}
                          meId={me.id}
                          refreshKey={version}
                          onOpen={setDrawerTask}
                          onEdit={(t) => setTaskModal({ open: true, task: t })}
                          onChanged={refresh}
                        />
                      ),
                    },
                    {
                      key: 'activity',
                      label: (
                        <span>
                          <HistoryOutlined /> Activity
                        </span>
                      ),
                      children: <ActivityTab projectId={projectId} />,
                    },
                  ]}
                />
              </Card>
            </Col>
            <Col xs={24}>
              <MembersCard
                projectId={projectId}
                members={members.data ?? []}
                canManage={canManage}
                onChanged={refreshAll}
              />
            </Col>
          </Row>

          <TaskFormModal
            open={taskModal.open}
            mode={canManage ? 'manage' : 'self'}
            projectId={projectId}
            task={taskModal.task}
            members={members.data ?? []}
            onClose={() => setTaskModal({ open: false, task: null })}
            onSaved={refresh}
          />
          <TaskDrawer task={drawerTask} onClose={() => setDrawerTask(null)} />
        </>
      )}
    </QueryState>
  )
}
