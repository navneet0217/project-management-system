import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { Alert, Button, Form, Input } from 'antd'
import { LockOutlined, MailOutlined } from '@ant-design/icons'
import AuthShell from '../components/AuthShell'
import { login } from '../store/authSlice'
import { authApi } from '../api/auth'
import { useAppDispatch } from '../store'
import { errorMessage } from '../api/axios'
import { APP_NAME } from '../components/Logo'

export default function Login() {
  const dispatch = useAppDispatch()
  const navigate = useNavigate()
  const location = useLocation()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [unverified, setUnverified] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)

  const from = (location.state as { from?: { pathname: string } } | null)?.from?.pathname ?? '/'

  const onFinish = async (values: { email: string; password: string }) => {
    setLoading(true)
    setError(null)
    setNotice(null)
    setUnverified(null)
    try {
      await dispatch(login(values)).unwrap()
      navigate(from, { replace: true })
    } catch (e) {
      const msg = errorMessage(e)
      setError(msg)
      if (msg.toLowerCase().includes('verify your email')) setUnverified(values.email)
    } finally {
      setLoading(false)
    }
  }

  const resend = async () => {
    if (!unverified) return
    await authApi.resendVerification(unverified).catch(() => undefined)
    setNotice('If that account needs verifying, a new link is on its way.')
  }

  return (
    <AuthShell
      title="Welcome back"
      subtitle={`Sign in to continue to ${APP_NAME}`}
      footer={
        <>
          New here? <Link to="/signup">Create an account</Link>
        </>
      }
    >
      {error && (
        <Alert
          type="error"
          title={error}
          showIcon
          style={{ marginBottom: 16 }}
          action={unverified && <Button size="small" onClick={resend}>Resend link</Button>}
        />
      )}
      {notice && <Alert type="success" title={notice} showIcon style={{ marginBottom: 16 }} />}
      <Form layout="vertical" onFinish={onFinish} requiredMark={false} size="large">
        <Form.Item
          name="email"
          label="Email"
          rules={[{ required: true, type: 'email', message: 'Enter a valid email' }]}
        >
          <Input prefix={<MailOutlined />} placeholder="you@company.com" autoComplete="username" />
        </Form.Item>
        <Form.Item
          name="password"
          label="Password"
          rules={[{ required: true, message: 'Enter your password' }]}
        >
          <Input.Password
            prefix={<LockOutlined />}
            placeholder="Your password"
            autoComplete="current-password"
          />
        </Form.Item>
        <div style={{ textAlign: 'right', marginTop: -12, marginBottom: 16 }}>
          <Link to="/forgot-password">Forgot password?</Link>
        </div>
        <Button type="primary" htmlType="submit" block loading={loading}>
          Sign in
        </Button>
      </Form>
    </AuthShell>
  )
}
