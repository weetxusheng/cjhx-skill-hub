import {
  AppstoreOutlined,
  AuditOutlined,
  DashboardOutlined,
  FolderOpenOutlined,
  PlusOutlined,
  OrderedListOutlined,
  RocketOutlined,
  SafetyOutlined,
  TeamOutlined,
  HistoryOutlined,
} from "@ant-design/icons";
import { Badge, Button, Layout, Menu, Space, Typography } from "antd";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";

type AdminLayoutProps = {
  user: {
    display_name: string;
    roles: string[];
    permissions: string[];
  };
  onLogout: () => void;
  loggingOut: boolean;
};

import { hasPermission } from "../lib/permissions";

const menuItems = [
  {
    key: "/",
    icon: <DashboardOutlined />,
    label: <NavLink to="/">Dashboard</NavLink>,
    permission: "admin.dashboard.view",
  },
  {
    key: "/skills",
    icon: <AppstoreOutlined />,
    label: <NavLink to="/skills">技能列表</NavLink>,
    permission: "skill.view",
  },
  {
    key: "/reviews",
    icon: <OrderedListOutlined />,
    label: <NavLink to="/reviews">审核中心</NavLink>,
    permission: "skill.review",
  },
  {
    key: "/releases",
    icon: <RocketOutlined />,
    label: <NavLink to="/releases">待发布</NavLink>,
    permission: "skill.publish",
  },
  {
    key: "/review-history",
    icon: <HistoryOutlined />,
    label: <NavLink to="/review-history">处理记录</NavLink>,
    permission: "skill.view",
  },
  {
    key: "/categories",
    icon: <FolderOpenOutlined />,
    label: <NavLink to="/categories">分类管理</NavLink>,
    permission: "admin.categories.view",
  },
  {
    key: "/users",
    icon: <TeamOutlined />,
    label: <NavLink to="/users">用户管理</NavLink>,
    permission: "admin.users.view",
  },
  {
    key: "/roles",
    icon: <SafetyOutlined />,
    label: <NavLink to="/roles">角色管理</NavLink>,
    permission: "admin.roles.view",
  },
  {
    key: "/audit-logs",
    icon: <AuditOutlined />,
    label: <NavLink to="/audit-logs">审计日志</NavLink>,
    permission: "admin.audit.view",
  },
];

export function AdminLayout({ user, onLogout, loggingOut }: AdminLayoutProps) {
  const location = useLocation();
  const navigate = useNavigate();
  const visibleMenuItems = menuItems.filter((item) => hasPermission(user, item.permission));
  const selectedKey = visibleMenuItems
    .map((item) => item.key)
    .find((key) => location.pathname === key || location.pathname.startsWith(`${key}/`))
    ?? "/";
  const canUpload = hasPermission(user, "skill.upload");

  return (
    <Layout className="admin-shell">
      <Layout.Sider theme="light" width={240} className="admin-sider">
        <Typography.Title level={4}>Skill Hub Admin</Typography.Title>
        <Typography.Paragraph className="sider-copy">
          当前阶段聚焦生产化落地，前后台已进入可运营、可审计、可部署的交付收口阶段。
        </Typography.Paragraph>
        <Menu mode="inline" selectedKeys={[selectedKey]} items={visibleMenuItems} className="admin-menu" />
      </Layout.Sider>
      <Layout>
        <Layout.Header className="admin-header">
          <div className="admin-header-left">
            <Badge status="processing" text="Skill Hub 生产化收口中" />
          </div>
          <div className="admin-header-actions">
            {canUpload ? (
              <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate("/skills?upload=1")}>
                上传技能
              </Button>
            ) : null}
            <Typography.Text>
              {user.display_name} · {user.roles.join(" / ")}
            </Typography.Text>
            <Button onClick={onLogout} loading={loggingOut}>
              退出登录
            </Button>
          </div>
        </Layout.Header>
        <Layout.Content className="admin-content">
          <Outlet />
        </Layout.Content>
      </Layout>
    </Layout>
  );
}
