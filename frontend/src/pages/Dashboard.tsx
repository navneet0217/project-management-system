import { Link } from 'react-router-dom'
import { Card, Col, Empty, List, Progress, Row, Skeleton, Tag, Typography, theme } from 'antd'
import {
  CheckCircleOutlined,
  ClockCircleOutlined,
  FolderOpenOutlined,
  ProfileOutlined,
  RocketOutlined,
  SyncOutlined,
  TeamOutlined,
  TrophyOutlined,
  UnorderedListOutlined,
  UserOutlined,
  WarningOutlined,
} from '@ant-design/icons'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { dashboardApi } from '../api/dashboard'
import { useFetch } from '../hooks/useFetch'
import { useAppSelector } from '../store'
import KpiCard from '../components/KpiCard'
import { KPI_DANGER, KPI_THEMES } from '../lib/kpiThemes'
import { BRAND, BRAND_LIGHT } from '../lib/brand'
import QueryState from '../components/QueryState'
import { StatusTag } from '../components/StatusTag'
import { PRIORITY_COLORS, STATUS_COLORS, label } from '../lib/options'

const KPI_ICONS: Record<string, React.ReactNode> = {
  total_users: <UserOutlined />,
  total_projects: <FolderOpenOutlined />,
  active_projects: <RocketOutlined />,
  completed_projects: <TrophyOutlined />,
  managed_projects: <FolderOpenOutlined />,
  team_members: <TeamOutlined />,
  assigned_tasks: <ProfileOutlined />,
  total_tasks: <UnorderedListOutlined />,
  pending_tasks: <ClockCircleOutlined />,
  in_progress_tasks: <SyncOutlined />,
  completed_tasks: <CheckCircleOutlined />,
  overdue_tasks: <WarningOutlined />,
}

const fetcher = () => dashboardApi.get()
const HIDDEN_KPIS = new Set(['completed_projects'])

const greeting = () => {
  const h = new Date().getHours()
  return h < 12 ? 'Good morning' : h < 18 ? 'Good afternoon' : 'Good evening'
}

export default function Dashboard() {
  const user = useAppSelector((s) => s.auth.user)!
  const { token } = theme.useToken()
  const tooltipStyle = {
    contentStyle: {
      background: token.colorBgElevated,
      border: `1px solid ${token.colorBorderSecondary}`,
      borderRadius: 8,
    },
    labelStyle: { color: token.colorText },
    itemStyle: { color: token.colorText },
  }
  const { data, loading, error, reload } = useFetch(fetcher)

  const statusData = Object.entries(data?.tasks_by_status ?? {}).map(([k, v]) => ({
    name: label(k),
    key: k,
    value: v,
  }))
  const priorityData = Object.entries(data?.tasks_by_priority ?? {}).map(([k, v]) => ({
    name: label(k),
    key: k,
    value: v,
  }))
  const hasTasks = statusData.some((d) => d.value > 0)

  // 8 cards (4 x 2) read cleaner than 9; "completed projects" is the least useful and wraps onto two lines
  const kpis = Object.entries(data?.summary ?? {}).filter(([k]) => !HIDDEN_KPIS.has(k))

  return (
    <QueryState loading={false} error={error} onRetry={reload}>
      <div className="page-head">
        <div>
          <Typography.Title level={3} style={{ margin: 0 }}>
            {greeting()}, {user.full_name.split(' ')[0]}
          </Typography.Title>
        </div>
        <Tag color="blue">{label(user.role)}</Tag>
      </div>

      {loading && !data ? (
        <div className="kpi-grid">
          {Array.from({ length: 6 }).map((_, i) => (
            <Card key={i} size="small">
              <Skeleton active title={{ width: '60%' }} paragraph={{ rows: 1 }} />
            </Card>
          ))}
        </div>
      ) : (
        <>
          <div className="kpi-grid">
            {kpis.map(([k, v], i) => (
              <KpiCard
                key={k}
                title={label(k)}
                value={v}
                icon={KPI_ICONS[k] ?? <UnorderedListOutlined />}
                theme={k === 'overdue_tasks' ? KPI_DANGER : KPI_THEMES[i % 4]}
              />
            ))}
          </div>

          <Row gutter={[20, 20]} style={{ marginTop: 20 }}>
            <Col xs={24} lg={12}>
              <Card title="Tasks by status" className="soft-card">
                {hasTasks ? (
                  <ResponsiveContainer width="100%" height={260}>
                    <PieChart>
                      <Pie
                        data={statusData}
                        dataKey="value"
                        nameKey="name"
                        innerRadius={55}
                        outerRadius={95}
                        paddingAngle={3}
                        stroke={token.colorBgContainer}
                      >
                        {statusData.map((d) => (
                          <Cell key={d.key} fill={STATUS_COLORS[d.key]} />
                        ))}
                      </Pie>
                      <Tooltip {...tooltipStyle} />
                    </PieChart>
                  </ResponsiveContainer>
                ) : (
                  <Empty description="No tasks yet" />
                )}
                <div className="legend">
                  {statusData.map((d) => (
                    <span key={d.key}>
                      <i style={{ background: STATUS_COLORS[d.key] }} /> {d.name} ({d.value})
                    </span>
                  ))}
                </div>
              </Card>
            </Col>
            <Col xs={24} lg={12}>
              <Card title="Tasks by priority" className="soft-card">
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={priorityData}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} opacity={0.4} />
                    <XAxis dataKey="name" axisLine={false} tickLine={false} />
                    <YAxis allowDecimals={false} axisLine={false} tickLine={false} />
                    <Tooltip cursor={{ opacity: 0.08 }} {...tooltipStyle} />
                    <Bar dataKey="value" radius={[8, 8, 0, 0]}>
                      {priorityData.map((d) => (
                        <Cell key={d.key} fill={PRIORITY_COLORS[d.key]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </Card>
            </Col>
          </Row>

          <Row gutter={[20, 20]} style={{ marginTop: 24 }}>
            <Col xs={24} lg={12}>
              <Card title="Project progress" className="soft-card">
                <List
                  dataSource={data?.projects ?? []}
                  locale={{ emptyText: <Empty description="No projects yet" /> }}
                  renderItem={(p) => (
                    <List.Item>
                      <div style={{ width: '100%' }}>
                        <Link to={`/projects/${p.id}`}>{p.name}</Link>
                        <Progress
                          percent={Math.round(p.completion_percentage)}
                          strokeColor={{ from: BRAND, to: BRAND_LIGHT }}
                        />
                      </div>
                    </List.Item>
                  )}
                />
              </Card>
            </Col>
            <Col xs={24} lg={12}>
              <Card title="Upcoming deadlines" className="soft-card">
                <List
                  dataSource={data?.upcoming_deadlines ?? []}
                  locale={{ emptyText: <Empty description="No upcoming deadlines" /> }}
                  renderItem={(d) => (
                    <List.Item extra={<StatusTag value={d.priority} />}>
                      <List.Item.Meta
                        title={<Link to={`/projects/${d.project_id}`}>{d.title}</Link>}
                        description={`${d.project_name} · due ${d.deadline}`}
                      />
                    </List.Item>
                  )}
                />
              </Card>
            </Col>
          </Row>
        </>
      )}
    </QueryState>
  )
}
