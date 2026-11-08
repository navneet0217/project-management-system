import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Button, Progress, Select, Space, Table } from 'antd'
import SearchInput from '../../../components/SearchInput'
import { PlusOutlined } from '@ant-design/icons'
import { projectsApi } from '../api'
import { useAppSelector } from '../../../store'
import { PageHeaderRow } from '../../../components/PageHeaderRow'
import ProjectFormModal from '../components/ProjectFormModal'
import { StatusTag } from '../../../components/StatusTag'
import { PROJECT_STATUSES, toOptions } from '../../../lib/options'
import type { Page, Project, ProjectStatus } from '../../../types'

export default function Projects() {
  const role = useAppSelector((s) => s.auth.user!.role)
  const [data, setData] = useState<Page<Project> | null>(null)
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState<ProjectStatus | undefined>()
  const [page, setPage] = useState(1)
  const [creating, setCreating] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      setData(await projectsApi.list({ search: search || undefined, status, page, size: 10 }))
    } finally {
      setLoading(false)
    }
  }, [search, status, page])

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load()
  }, [load])

  return (
    <>
      <PageHeaderRow
        title="Projects"
        extra={
          role !== 'DEVELOPER' && (
            <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreating(true)}>
              New project
            </Button>
          )
        }
      />
      <Space style={{ marginBottom: 16 }} wrap>
        <SearchInput
          placeholder="Search projects, managers, descriptions"
          width={340}
          onSearch={(v) => {
            setSearch(v)
            setPage(1)
          }}
        />
        <Select
          allowClear
          placeholder="Status"
          options={toOptions(PROJECT_STATUSES)}
          value={status}
          onChange={(v) => {
            setStatus(v)
            setPage(1)
          }}
          style={{ width: 160 }}
        />
      </Space>
      <Table<Project>
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
            title: 'Name',
            dataIndex: 'name',
            render: (n: string, p) => <Link to={`/projects/${p.id}`}>{n}</Link>,
          },
          {
            title: 'Status',
            dataIndex: 'status',
            render: (s: ProjectStatus) => <StatusTag value={s} />,
          },
          { title: 'Manager', render: (_, p) => p.manager?.full_name ?? '-' },
          { title: 'Members', dataIndex: 'member_count' },
          {
            title: 'Progress',
            width: 180,
            render: (_, p) => (
              <Progress
                percent={Math.round(p.completion_percentage)}
                size="small"
                format={() => `${p.done_tasks}/${p.total_tasks}`}
              />
            ),
          },
          { title: 'Ends', dataIndex: 'end_date', render: (d: string | null) => d ?? '-' },
        ]}
      />
      <ProjectFormModal
        open={creating}
        project={null}
        onClose={() => setCreating(false)}
        onSaved={load}
      />
    </>
  )
}
