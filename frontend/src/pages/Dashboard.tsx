import { Link } from 'react-router-dom'
import { Card, Col, List, Progress, Row, Statistic, Typography } from 'antd'
import { Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { dashboardApi } from '../api/dashboard'
import { useFetch } from '../hooks/useFetch'
import QueryState from '../components/QueryState'
import { StatusTag, label } from '../components/StatusTag'

const STATUS_COLORS: Record<string, string> = {
  TODO: '#8c8c8c',
  IN_PROGRESS: '#1677ff',
  IN_REVIEW: '#722ed1',
  DONE: '#52c41a',
}

const fetcher = () => dashboardApi.get()

export default function Dashboard() {
  const { data, loading, error, reload } = useFetch(fetcher)

  const statusData = Object.entries(data?.tasks_by_status ?? {}).map(([k, v]) => ({
    name: label(k),
    key: k,
    value: v,
  }))
  const priorityData = Object.entries(data?.tasks_by_priority ?? {}).map(([k, v]) => ({
    name: label(k),
    value: v,
  }))

  return (
    <QueryState loading={loading} error={error} onRetry={reload}>
      <Typography.Title level={3}>Dashboard</Typography.Title>
      <Row gutter={[16, 16]}>
        {Object.entries(data?.summary ?? {}).map(([k, v]) => (
          <Col key={k} xs={12} md={8} xl={6}>
            <Card>
              <Statistic title={label(k)} value={v} />
            </Card>
          </Col>
        ))}
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={12}>
          <Card title="Tasks by status">
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie data={statusData} dataKey="value" nameKey="name" label>
                  {statusData.map((d) => (
                    <Cell key={d.key} fill={STATUS_COLORS[d.key]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="Tasks by priority">
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={priorityData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="value" fill="#1677ff" />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={12}>
          <Card title="Project progress">
            <List
              dataSource={data?.projects ?? []}
              locale={{ emptyText: 'No projects yet' }}
              renderItem={(p) => (
                <List.Item>
                  <div style={{ width: '100%' }}>
                    <Link to={`/projects/${p.id}`}>{p.name}</Link>
                    <Progress percent={Math.round(p.completion_percentage)} />
                  </div>
                </List.Item>
              )}
            />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="Upcoming deadlines">
            <List
              dataSource={data?.upcoming_deadlines ?? []}
              locale={{ emptyText: 'No upcoming deadlines' }}
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
    </QueryState>
  )
}
