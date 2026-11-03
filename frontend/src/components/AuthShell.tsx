import { Typography } from 'antd'
import {
  CheckCircleFilled,
  DashboardOutlined,
  ProjectOutlined,
  TeamOutlined,
} from '@ant-design/icons'

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
  return (
    <div className="auth-shell">
      <aside className="auth-brand">
        <div className="auth-brand-inner">
          <div className="auth-logo">
            <CheckCircleFilled /> ProjectHub
          </div>
          <Typography.Title level={2} style={{ color: '#fff', marginTop: 32 }}>
            Ship projects, not spreadsheets.
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
