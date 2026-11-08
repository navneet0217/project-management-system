import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Alert, Button, Form, Input } from 'antd'
import { MailOutlined } from '@ant-design/icons'
import AuthShell from '../../../components/AuthShell'
import { authApi } from '../api'
import { errorMessage } from '../../../api/axios'

export default function ForgotPassword() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [done, setDone] = useState(false)

  const onFinish = async ({ email }: { email: string }) => {
    setLoading(true)
    setError(null)
    try {
      await authApi.forgotPassword(email)
      setDone(true)
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthShell
      title="Forgot your password?"
      subtitle="Enter your email and we will send you a reset link."
      footer={<Link to="/login">Back to sign in</Link>}
    >
      {done ? (
        <Alert
          type="success"
          showIcon
          title="If that email has an account, a reset link is on its way. It is valid for 30 minutes."
        />
      ) : (
        <>
          {error && <Alert type="error" title={error} showIcon style={{ marginBottom: 16 }} />}
          <Form layout="vertical" onFinish={onFinish} requiredMark={false} size="large">
            <Form.Item
              name="email"
              label="Email"
              rules={[{ required: true, type: 'email', message: 'Enter a valid email' }]}
            >
              <Input prefix={<MailOutlined />} placeholder="you@company.com" autoComplete="email" />
            </Form.Item>
            <Button type="primary" htmlType="submit" block loading={loading}>
              Send reset link
            </Button>
          </Form>
        </>
      )}
    </AuthShell>
  )
}
