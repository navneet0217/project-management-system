import { Modal } from 'antd'
import UserDetails from './UserDetails'
import { useUserProfile } from '../hooks/useUserProfile'

// "View profile" popup on the Users screen.
export default function UserProfileModal({ userId, onClose }: { userId: number | null; onClose: () => void }) {
  const { profile, loading, error } = useUserProfile(userId)
  return (
    <Modal
      open={userId !== null}
      onCancel={onClose}
      footer={null}
      centered
      width={760}
      destroyOnHidden
      title={profile ? `${profile.user.full_name} - profile` : 'User profile'}
      styles={{ body: { maxHeight: '70vh', overflowY: 'auto' } }}
    >
      <UserDetails profile={profile} loading={loading} error={error} />
    </Modal>
  )
}
