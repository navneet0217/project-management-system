import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { Alert, Button, Form, Input } from 'antd'
import { LockOutlined } from '@ant-design/icons'
import AuthShell from '../../../components/AuthShell'
import { authApi } from '../api'
import { errorMessage } from '../../../api/axios'

export default function ResetPassword() {
  const token = useSearchParams()[0].get('token') ?? ''
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [done, setDone] = useState(false)

  const onFinish = async ({ password }: { password: string; confirm: string }) => {
    setLoading(true)
    setError(null)
    try {
      await authApi.resetPassword(token, password)
      setDone(true)
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthShell
      title="Choose a new password"
      subtitle="You will be signed out everywhere else."
      footer={<Link to="/login">Back to sign in</Link>}
    >
      {!token ? (
        <Alert type="error" showIcon title="This reset link is missing its token. Request a new one." />
      ) : done ? (
        <Alert type="success" showIcon title="Password updated. You can sign in now." />
      ) : (
        <>
          {error && <Alert type="error" title={error} showIcon style={{ marginBottom: 16 }} />}
          <Form layout="vertical" onFinish={onFinish} requiredMark={false} size="large">
            <Form.Item
              name="password"
              label="New password"
              extra="At least 8 characters, with a letter and a number"
              rules={[
                { required: true, min: 8, max: 128, message: 'At least 8 characters' },
                { pattern: /^(?=.*[A-Za-z])(?=.*\d).+$/, message: 'Must contain a letter and a number' },
              ]}
            >
              <Input.Password prefix={<LockOutlined />} autoComplete="new-password" />
            </Form.Item>
            <Form.Item
              name="confirm"
              label="Confirm password"
              dependencies={['password']}
              rules={[
                { required: true, message: 'Confirm your password' },
                ({ getFieldValue }) => ({
                  validator: (_, value) =>
                    !value || getFieldValue('password') === value
                      ? Promise.resolve()
                      : Promise.reject(new Error('Passwords do not match')),
                }),
              ]}
            >
              <Input.Password prefix={<LockOutlined />} autoComplete="new-password" />
            </Form.Item>
            <Button type="primary" htmlType="submit" block loading={loading}>
              Update password
            </Button>
          </Form>
        </>
      )}
    </AuthShell>
  )
}
