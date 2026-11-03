import { useMemo } from 'react'
import { Outlet, useLocation, useNavigate } from 'react-router-dom'
import { Avatar, Button, Dropdown, Layout, Menu, Space, Typography, theme } from 'antd'
import {
  CheckSquareOutlined,
  DashboardOutlined,
  FolderOpenOutlined,
  LogoutOutlined,
  MoonOutlined,
  SunOutlined,
  TeamOutlined,
} from '@ant-design/icons'
import { logout } from '../store/authSlice'
import { setSiderCollapsed, toggleDarkMode } from '../store/uiSlice'
import { useAppDispatch, useAppSelector } from '../store'
import { StatusTag } from '../components/StatusTag'

const { Header, Sider, Content } = Layout

export default function AppLayout() {
  const dispatch = useAppDispatch()
  const navigate = useNavigate()
  const { pathname } = useLocation()
  const { token } = theme.useToken()
  const user = useAppSelector((s) => s.auth.user)!
  const { darkMode, siderCollapsed } = useAppSelector((s) => s.ui)

  // Navigation is filtered by role for convenience only; the backend enforces RBAC.
  const items = useMemo(() => {
    const all = [
      { key: '/', icon: <DashboardOutlined />, label: 'Dashboard' },
      { key: '/projects', icon: <FolderOpenOutlined />, label: 'Projects' },
      { key: '/my-tasks', icon: <CheckSquareOutlined />, label: 'My tasks' },
    ]
    if (user.role === 'ADMIN') all.push({ key: '/users', icon: <TeamOutlined />, label: 'Users' })
    return all
  }, [user.role])

  const selected = items
    .filter((i) => (i.key === '/' ? pathname === '/' : pathname.startsWith(i.key)))
    .map((i) => i.key)

  const onLogout = async () => {
    await dispatch(logout())
    navigate('/login', { replace: true })
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        collapsible
        collapsed={siderCollapsed}
        onCollapse={(c) => dispatch(setSiderCollapsed(c))}
        breakpoint="lg"
      >
        <Typography.Title
          level={4}
          style={{ color: '#fff', textAlign: 'center', margin: 16, whiteSpace: 'nowrap' }}
        >
          {siderCollapsed ? 'PM' : 'ProjectHub'}
        </Typography.Title>
        <Menu
          theme="dark"
          mode="inline"
          items={items}
          selectedKeys={selected}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <Layout>
        <Header
          style={{
            background: token.colorBgContainer,
            padding: '0 24px',
            display: 'flex',
            justifyContent: 'flex-end',
            alignItems: 'center',
            gap: 12,
          }}
        >
          <Button
            type="text"
            aria-label="Toggle dark mode"
            icon={darkMode ? <SunOutlined /> : <MoonOutlined />}
            onClick={() => dispatch(toggleDarkMode())}
          />
          <Dropdown
            menu={{
              items: [{ key: 'logout', icon: <LogoutOutlined />, label: 'Log out' }],
              onClick: onLogout,
            }}
          >
            <Space style={{ cursor: 'pointer' }}>
              <Avatar>{user.full_name.charAt(0).toUpperCase()}</Avatar>
              <span>{user.full_name}</span>
              <StatusTag value={user.role} />
            </Space>
          </Dropdown>
        </Header>
        <Content style={{ margin: 24 }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}

