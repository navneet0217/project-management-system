import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Alert, Button, Form, Input } from 'antd'
import { LockOutlined, MailOutlined, UserOutlined } from '@ant-design/icons'
import AuthShell from '../../../components/AuthShell'
import { authApi } from '../api'
import { errorMessage } from '../../../api/axios'
import { APP_NAME } from '../../../components/Logo'

interface SignupForm {
  full_name: string
  email: string
  password: string
  confirm: string
}

export default function Signup() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [done, setDone] = useState<string | null>(null)

  const onFinish = async ({ full_name, email, password }: SignupForm) => {
    setLoading(true)
    setError(null)
    try {
      const res = await authApi.signup({ full_name, email, password })
      setDone(res.detail)
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setLoading(false)
    }
  }

  if (done) {
    return (
      <AuthShell title="Account created" subtitle="" footer={<Link to="/login">Go to sign in</Link>}>
        <Alert type="success" showIcon title={done} />
      </AuthShell>
    )
  }

  return (
    <AuthShell
      title="Create your account"
      subtitle={`Join your team on ${APP_NAME}. New accounts start as developers.`}
      footer={
        <>
          Already have an account? <Link to="/login">Sign in</Link>
        </>
      }
    >
      {error && <Alert type="error" title={error} showIcon style={{ marginBottom: 16 }} />}
      <Form<SignupForm> layout="vertical" onFinish={onFinish} requiredMark={false} size="large">
        <Form.Item
          name="full_name"
          label="Full name"
          rules={[{ required: true, min: 2, max: 120, message: 'Enter your name (2-120 characters)' }]}
        >
          <Input prefix={<UserOutlined />} placeholder="Jane Doe" autoComplete="name" />
        </Form.Item>
        <Form.Item
          name="email"
          label="Email"
          rules={[{ required: true, type: 'email', message: 'Enter a valid email' }]}
        >
          <Input prefix={<MailOutlined />} placeholder="you@company.com" autoComplete="email" />
        </Form.Item>
        <Form.Item
          name="password"
          label="Password"
          extra="At least 8 characters, with a letter and a number"
          rules={[
            { required: true, min: 8, max: 128, message: 'At least 8 characters' },
            {
              pattern: /^(?=.*[A-Za-z])(?=.*\d).+$/,
              message: 'Must contain a letter and a number',
            },
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
          Create account
        </Button>
      </Form>
    </AuthShell>
  )
}
