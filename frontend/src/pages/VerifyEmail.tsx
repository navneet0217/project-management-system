import { useEffect, useRef, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { Alert, Spin } from 'antd'
import AuthShell from '../components/AuthShell'
import { authApi } from '../api/auth'
import { errorMessage } from '../api/axios'

export default function VerifyEmail() {
  const token = useSearchParams()[0].get('token')
  const [state, setState] = useState<{ ok: boolean; msg: string } | null>(
    token ? null : { ok: false, msg: 'This link is missing its token.' },
  )
  const started = useRef(false)

  useEffect(() => {
    // tokens are single-use, so guard against React StrictMode running the effect twice
    if (!token || started.current) return
    started.current = true
    authApi
      .verifyEmail(token)
      .then(() => setState({ ok: true, msg: 'Email verified. You can sign in now.' }))
      .catch((e) => setState({ ok: false, msg: errorMessage(e) }))
  }, [token])

  return (
    <AuthShell title="Email verification" subtitle="" footer={<Link to="/login">Go to sign in</Link>}>
      {state ? <Alert type={state.ok ? 'success' : 'error'} showIcon title={state.msg} /> : <Spin />}
    </AuthShell>
  )
}
