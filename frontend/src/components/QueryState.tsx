import { Alert, Button, Spin } from 'antd'

export default function QueryState({
  loading,
  error,
  onRetry,
  children,
}: {
  loading: boolean
  error: boolean
  onRetry: () => void
  children: React.ReactNode
}) {
  if (error) {
    return (
      <Alert
        type="error"
        showIcon
        message="Could not load data"
        action={<Button onClick={onRetry}>Retry</Button>}
      />
    )
  }
  return <Spin spinning={loading}>{children}</Spin>
}
