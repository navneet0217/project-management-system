import { Link } from 'react-router-dom'
import { Alert, Descriptions, Empty, Skeleton, Table, Tag, Typography } from 'antd'
import ActivityTimeline from '../../projects/components/ActivityTimeline'
import { StatusTag } from '../../../components/StatusTag'
import { formatDate } from '../../../lib/dates'
import type { ProfileProject, Task, UserProfile } from '../../../types'

function ProjectTags({ projects, empty }: { projects: ProfileProject[]; empty: string }) {
  if (projects.length === 0) return <Typography.Text type="secondary">{empty}</Typography.Text>
  return (
    <div className="chip-row">
      {projects.map((p) => (
        <Tag key={`${p.id}-${p.relation}`} color={p.relation === 'Removed' ? 'default' : 'teal'}>
          <Link to={`/projects/${p.id}`}>{p.name}</Link>
          {p.relation !== 'Member' && <span className="chip-note"> ({p.relation.toLowerCase()})</span>}
        </Tag>
      ))}
    </div>
  )
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="profile-section">
      <h4>{title}</h4>
      {children}
    </section>
  )
}

// Read-only overview of a user: basics, role, manager, projects, tasks and (optionally) activity.
export default function UserDetails({
  profile,
  loading,
  error,
  showActivity = true,
}: {
  profile: UserProfile | null
  loading: boolean
  error: boolean
  showActivity?: boolean
}) {
  if (error) return <Alert type="error" showIcon title="Could not load user details" />
  if (loading || !profile) return <Skeleton active paragraph={{ rows: 8 }} />

  const { user } = profile
  return (
    <div className="profile">
      <Section title="Basic information">
        <Descriptions column={{ xs: 1, sm: 2 }} size="small">
          <Descriptions.Item label="Name">{user.full_name}</Descriptions.Item>
          <Descriptions.Item label="Email">{user.email}</Descriptions.Item>
          <Descriptions.Item label="Status">
            <Tag color={user.is_active ? 'success' : 'default'}>{user.is_active ? 'Active' : 'Inactive'}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Member since">{formatDate(user.created_at)}</Descriptions.Item>
        </Descriptions>
      </Section>

      <Section title="Role">
        <StatusTag value={user.role} />
      </Section>

      <Section title="Manager">
        {profile.managers.length ? (
          profile.managers.map((m) => <Tag key={m.id}>{m.full_name}</Tag>)
        ) : (
          <Typography.Text type="secondary">No reporting manager (not on any active project)</Typography.Text>
        )}
      </Section>

      <Section title={`Current projects (${profile.current_projects.length})`}>
        <ProjectTags projects={profile.current_projects} empty="Not on any active project" />
      </Section>

      <Section title={`Past projects (${profile.past_projects.length})`}>
        <ProjectTags projects={profile.past_projects} empty="No past projects" />
      </Section>

      <Section title={`Tasks (${profile.tasks.length})`}>
        <Table<Task>
          size="small"
          rowKey="id"
          dataSource={profile.tasks}
          pagination={false}
          scroll={{ x: 'max-content', y: 220 }}
          locale={{ emptyText: <Empty description="No tasks assigned" image={Empty.PRESENTED_IMAGE_SIMPLE} /> }}
          columns={[
            { title: 'Task', dataIndex: 'title' },
            { title: 'Project', dataIndex: 'project_name' },
            { title: 'Status', dataIndex: 'status', render: (v: string) => <StatusTag value={v} /> },
            { title: 'Priority', dataIndex: 'priority', render: (v: string) => <StatusTag value={v} /> },
            {
              title: 'Deadline',
              dataIndex: 'deadline',
              render: (_, t) => (
                <>
                  {t.deadline ?? '-'}
                  {t.is_overdue && <Tag color="red">Overdue</Tag>}
                </>
              ),
            },
          ]}
        />
      </Section>

      {showActivity && (
        <Section title="Activity">
          <ActivityTimeline items={profile.activity} showProject />
        </Section>
      )}
    </div>
  )
}
