import { Suspense, useMemo } from 'react'
import { Outlet, useLocation, useNavigate } from 'react-router-dom'
import { Avatar, Button, Dropdown, Grid, Layout, Menu, Skeleton, Space, Tooltip, theme } from 'antd'
import {
  CheckSquareOutlined,
  DashboardOutlined,
  FolderOpenOutlined,
  LogoutOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  MoonOutlined,
  SunOutlined,
  TeamOutlined,
} from '@ant-design/icons'
import { logout } from '../store/authSlice'
import { setSiderCollapsed, toggleDarkMode } from '../store/uiSlice'
import { useAppDispatch, useAppSelector } from '../store'
import { StatusTag } from '../components/StatusTag'
import GlobalSearch from '../components/GlobalSearch'
import Logo, { APP_NAME } from '../components/Logo'
import { BRAND_GRADIENT } from '../lib/brand'

const { Header, Sider, Content } = Layout

export default function AppLayout() {
  const dispatch = useAppDispatch()
  const navigate = useNavigate()
  const { pathname } = useLocation()
  const { token } = theme.useToken()
  const screens = Grid.useBreakpoint()
  const isMobile = !screens.lg
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
        className="app-sider"
        width={240}
        collapsedWidth={isMobile ? 0 : 76}
        collapsed={isMobile ? true : siderCollapsed}
        trigger={null}
      >
        <div className="sider-logo">
          <Logo size={34} />
          {!siderCollapsed && !isMobile && <span>{APP_NAME}</span>}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          items={items}
          selectedKeys={selected}
          onClick={({ key }) => navigate(key)}
          style={{ background: 'transparent', borderInlineEnd: 0, flex: 1 }}
        />
        {!isMobile && (
          <Tooltip title={siderCollapsed ? 'Expand sidebar' : ''} placement="right">
            <button
              type="button"
              className="sider-toggle"
              aria-label={siderCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
              onClick={() => dispatch(setSiderCollapsed(!siderCollapsed))}
            >
              {siderCollapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
              {!siderCollapsed && <span>Collapse</span>}
            </button>
          </Tooltip>
        )}
      </Sider>
      <Layout style={{ background: 'transparent' }}>
        <Header
          className="app-header"
          style={{ borderBottom: `1px solid ${token.colorBorderSecondary}` }}
        >
          <GlobalSearch />
          <Tooltip title={darkMode ? 'Light mode' : 'Dark mode'}>
            <Button
              type="text"
              shape="circle"
              aria-label="Toggle dark mode"
              icon={darkMode ? <SunOutlined /> : <MoonOutlined />}
              onClick={() => dispatch(toggleDarkMode())}
            />
          </Tooltip>
          <Dropdown
            menu={{
              items: [{ key: 'logout', icon: <LogoutOutlined />, label: 'Log out' }],
              onClick: onLogout,
            }}
          >
            <Space style={{ cursor: 'pointer' }}>
              <Avatar style={{ background: BRAND_GRADIENT }}>
                {user.full_name.charAt(0).toUpperCase()}
              </Avatar>
              {!isMobile && <span>{user.full_name}</span>}
              {!isMobile && <StatusTag value={user.role} />}
            </Space>
          </Dropdown>
        </Header>
        <Content className="app-content">
          {/* key = path, so every page change replays the fade-in animation */}
          <div key={pathname} className="page-fade">
            <Suspense fallback={<Skeleton active paragraph={{ rows: 8 }} />}>
              <Outlet />
            </Suspense>
          </div>
        </Content>
        {isMobile && (
          <nav className="mobile-nav" aria-label="Main navigation">
            {items.map((i) => (
              <button
                key={i.key}
                type="button"
                className={selected.includes(i.key) ? 'active' : ''}
                onClick={() => navigate(i.key)}
              >
                {i.icon}
                <span>{i.label}</span>
              </button>
            ))}
          </nav>
        )}
      </Layout>
    </Layout>
  )
}
