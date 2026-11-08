import { useState } from 'react'
import { Button, Modal, Space } from 'antd'
import { projectsApi } from '../api'
import UserDetails from '../../users/components/UserDetails'
import { useUserProfile } from '../../users/hooks/useUserProfile'

// Shown after picking a developer in the member dropdown: review their details, then Cancel or Add.
export default function AddMemberModal({
  projectId,
  userId,
  alreadyMemberIds,
  onClose,
  onAdded,
}: {
  projectId: number
  userId: number | null
  alreadyMemberIds: number[]
  onClose: () => void
  onAdded: () => void
}) {
  const { profile, loading, error } = useUserProfile(userId)
  const [adding, setAdding] = useState(false)

  const isMember = userId !== null && alreadyMemberIds.includes(userId)
  const inactive = !!profile && !profile.user.is_active
  const blocker = isMember ? 'Already a member of this project' : inactive ? 'Inactive users cannot be added' : null

  const add = async () => {
    if (userId === null) return
    setAdding(true)
    try {
      await projectsApi.addMember(projectId, userId)
      onAdded()
      onClose()
    } catch {
      // the axios interceptor already showed the error
    } finally {
      setAdding(false)
    }
  }

  return (
    <Modal
      open={userId !== null}
      onCancel={onClose}
      centered
      width={720}
      destroyOnHidden
      title="Add member to project"
      styles={{ body: { maxHeight: '65vh', overflowY: 'auto' } }}
      footer={
        <div className="footer-left">
          <Space>
            <Button onClick={onClose}>Cancel</Button>
            <Button type="primary" onClick={add} loading={adding} disabled={!profile || !!blocker}>
              Add
            </Button>
            {blocker && <span className="footer-note">{blocker}</span>}
          </Space>
        </div>
      }
    >
      <UserDetails profile={profile} loading={loading} error={error} showActivity={false} />
    </Modal>
  )
}
