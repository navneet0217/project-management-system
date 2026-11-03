import { useEffect, useState } from 'react'
import { Avatar, Button, Card, List, Popconfirm, Select, Space, Tag } from 'antd'
import { projectsApi } from '../../api/projects'
import { usersApi } from '../../api/users'
import { BRAND } from '../../lib/brand'
import type { UserOption } from '../../types'

export default function MembersCard({
  projectId,
  members,
  canManage,
  onChanged,
}: {
  projectId: number
  members: UserOption[]
  canManage: boolean
  onChanged: () => void
}) {
  const [candidates, setCandidates] = useState<UserOption[]>([])
  const [selected, setSelected] = useState<number | undefined>()

  useEffect(() => {
    if (canManage) usersApi.options('DEVELOPER').then(setCandidates).catch(() => {})
  }, [canManage])

  const memberIds = new Set(members.map((m) => m.id))
  const addable = candidates.filter((c) => !memberIds.has(c.id))

  const add = async () => {
    if (!selected) return
    try {
      await projectsApi.addMember(projectId, selected)
      setSelected(undefined)
      onChanged()
    } catch {
      // error toast comes from the axios interceptor
    }
  }

  const remove = async (id: number) => {
    try {
      await projectsApi.removeMember(projectId, id)
      onChanged()
    } catch {
      // error toast comes from the axios interceptor
    }
  }

  return (
    <Card title={`Members (${members.length})`} className="soft-card">
      {canManage && (
        <Space style={{ marginBottom: 12 }} wrap>
          <Select
            showSearch
            optionFilterProp="label"
            placeholder="Add a developer"
            style={{ width: 240 }}
            value={selected}
            onChange={setSelected}
            options={addable.map((u) => ({ value: u.id, label: u.full_name }))}
          />
          <Button type="primary" disabled={!selected} onClick={add}>
            Add
          </Button>
        </Space>
      )}
      <List
        dataSource={members}
        locale={{ emptyText: 'No members yet' }}
        renderItem={(m) => (
          <List.Item
            actions={
              canManage
                ? [
                    <Popconfirm
                      key="rm"
                      title="Remove member? Their tasks here become unassigned."
                      onConfirm={() => remove(m.id)}
                    >
                      <Button size="small" danger>
                        Remove
                      </Button>
                    </Popconfirm>,
                  ]
                : undefined
            }
          >
            <List.Item.Meta
              avatar={<Avatar style={{ background: BRAND }}>{m.full_name.charAt(0)}</Avatar>}
              title={m.full_name}
              description={<Tag>{m.role}</Tag>}
            />
          </List.Item>
        )}
      />
    </Card>
  )
}
