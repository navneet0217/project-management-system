import { Button, Tooltip, Typography } from 'antd'
import {
  DashboardOutlined,
  MoonOutlined,
  ProjectOutlined,
  SunOutlined,
  TeamOutlined,
} from '@ant-design/icons'
import Logo, { APP_NAME } from './Logo'
import { toggleDarkMode } from '../store/uiSlice'
import { useAppDispatch, useAppSelector } from '../store'

const FEATURES = [
  { icon: <ProjectOutlined />, text: 'Plan projects and track every task' },
  { icon: <TeamOutlined />, text: 'Role-based access for admins, managers and developers' },
  { icon: <DashboardOutlined />, text: 'Live dashboards for progress and deadlines' },
]

// Split-screen layout shared by Login and Signup: brand panel on the left, form on the right.
export default function AuthShell({
  title,
  subtitle,
  children,
  footer,
}: {
  title: string
  subtitle: string
  children: React.ReactNode
  footer: React.ReactNode
}) {
  const dispatch = useAppDispatch()
  const darkMode = useAppSelector((s) => s.ui.darkMode)

  return (
    <div className="auth-shell">
      <Tooltip title={darkMode ? 'Light mode' : 'Dark mode'}>
        <Button
          className="theme-fab"
          shape="circle"
          aria-label="Toggle dark mode"
          icon={darkMode ? <SunOutlined /> : <MoonOutlined />}
          onClick={() => dispatch(toggleDarkMode())}
        />
      </Tooltip>
      <aside className="auth-brand">
        <div className="auth-brand-inner">
          <div className="auth-logo">
            <Logo size={40} /> {APP_NAME}
          </div>
          <Typography.Title level={2} style={{ color: '#fff', marginTop: 32 }}>
            Plan it. Track it. Ship it.
          </Typography.Title>
          <ul className="auth-features">
            {FEATURES.map((f) => (
              <li key={f.text}>
                <span className="auth-feature-icon">{f.icon}</span>
                {f.text}
              </li>
            ))}
          </ul>
        </div>
      </aside>

      <main className="auth-form-side">
        {/* Phones hide the big brand panel, so show the logo and tagline here instead */}
        <div className="auth-mobile-brand">
          <Logo size={44} />
          <div className="auth-mobile-name">{APP_NAME}</div>
          <div className="auth-mobile-tagline">Plan it. Track it. Ship it.</div>
        </div>
        <div className="auth-card">
          <Typography.Title level={2} style={{ marginBottom: 4 }}>
            {title}
          </Typography.Title>
          <Typography.Paragraph type="secondary">{subtitle}</Typography.Paragraph>
          {children}
          <div className="auth-footer">{footer}</div>
        </div>
      </main>
    </div>
  )
}
