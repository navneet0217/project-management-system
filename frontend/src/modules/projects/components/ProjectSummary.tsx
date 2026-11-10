import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button, Card, Descriptions, Popconfirm, Progress, Space, Tooltip, Typography, message } from 'antd'
import { DeleteOutlined, EditOutlined } from '@ant-design/icons'
import { projectsApi } from '../api'
import ProjectFormModal from './ProjectFormModal'
import { StatusTag } from '../../../components/StatusTag'
import { BRAND, BRAND_LIGHT } from '../../../lib/brand'
import type { Project } from '../../../types'

export default function ProjectSummary({
  project,
  canManage,
  onChanged,
}: {
  project: Project
  canManage: boolean
  onChanged: () => void
}) {
  const navigate = useNavigate()
  const [editing, setEditing] = useState(false)

  const remove = async () => {
    try {
      await projectsApi.remove(project.id)
      message.success('Project deleted')
      navigate('/projects')
    } catch {
      // error toast comes from the axios interceptor
    }
  }

  return (
    <>
      <div className="page-head">
        <Typography.Title level={2} style={{ margin: 0 }}>
          {project.name} <StatusTag value={project.status} />
        </Typography.Title>
        {canManage && (
          <Space>
            <Tooltip title="Edit project">
              <Button aria-label="Edit project" icon={<EditOutlined />} onClick={() => setEditing(true)} />
            </Tooltip>
            <Popconfirm
              title="Delete this project?"
              description="Projects with open tasks cannot be deleted."
              onConfirm={remove}
            >
              <Tooltip title="Delete project">
                <Button aria-label="Delete project" danger icon={<DeleteOutlined />} />
              </Tooltip>
            </Popconfirm>
          </Space>
        )}
      </div>

      <Card className="soft-card" style={{ marginBottom: 20 }}>
        <Descriptions column={{ xs: 1, md: 2 }}>
          <Descriptions.Item label="Description">{project.description || '-'}</Descriptions.Item>
          <Descriptions.Item label="Manager">{project.manager?.full_name ?? '-'}</Descriptions.Item>
          <Descriptions.Item label="Dates">
            {project.start_date ?? '?'} → {project.end_date ?? '?'}
          </Descriptions.Item>
          <Descriptions.Item label="Progress">
            <Progress
              percent={Math.round(project.completion_percentage)}
              size="small"
              strokeColor={{ from: BRAND, to: BRAND_LIGHT }}
              format={() => `${project.done_tasks}/${project.total_tasks}`}
            />
          </Descriptions.Item>
        </Descriptions>
      </Card>

      <ProjectFormModal
        open={editing}
        project={project}
        onClose={() => setEditing(false)}
        onSaved={onChanged}
      />
    </>
  )
}
