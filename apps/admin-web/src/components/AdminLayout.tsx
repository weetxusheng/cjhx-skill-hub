/**
 * 组件约定：
 * - 承载后台全局导航、工作台 tabs 与 Outlet，不直接承担页面级数据请求。
 * - 菜单显隐统一基于用户全局 permission；登出按钮只透传回调，不自行处理会话清理。
 */
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
import { Badge, Button, Layout, Menu, Tabs, Typography } from "antd";
import { type ReactNode, useEffect, useMemo, useState } from "react";
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

type WorkspaceTab = {
  key: string;
  path: string;
  label: string;
};

type NavItem = {
  key: string;
  icon: ReactNode;
  label: string;
  menuLabel: ReactNode;
  canAccess: (user: AdminLayoutProps["user"]) => boolean;
};

const navItems: NavItem[] = [
  {
    key: "/",
    icon: <DashboardOutlined />,
    label: "工作台",
    menuLabel: <NavLink to="/">工作台</NavLink>,
    canAccess: (user) =>
      hasPermission(user, "admin.dashboard.view")
      || hasPermission(user, "skill.view")
      || hasPermission(user, "skill.review")
      || hasPermission(user, "skill.publish"),
  },
  {
    key: "/skills",
    icon: <AppstoreOutlined />,
    label: "技能列表",
    menuLabel: <NavLink to="/skills">技能列表</NavLink>,
    canAccess: (user) => hasPermission(user, "skill.view"),
  },
  {
    key: "/reviews",
    icon: <OrderedListOutlined />,
    label: "审核中心",
    menuLabel: <NavLink to="/reviews">审核中心</NavLink>,
    canAccess: (user) => hasPermission(user, "skill.review"),
  },
  {
    key: "/releases",
    icon: <RocketOutlined />,
    label: "待发布",
    menuLabel: <NavLink to="/releases">待发布</NavLink>,
    canAccess: (user) => hasPermission(user, "skill.publish"),
  },
  {
    key: "/review-history",
    icon: <HistoryOutlined />,
    label: "处理记录",
    menuLabel: <NavLink to="/review-history">处理记录</NavLink>,
    canAccess: (user) => hasPermission(user, "skill.view"),
  },
  {
    key: "/categories",
    icon: <FolderOpenOutlined />,
    label: "分类管理",
    menuLabel: <NavLink to="/categories">分类管理</NavLink>,
    canAccess: (user) => hasPermission(user, "admin.categories.view"),
  },
  {
    key: "/users",
    icon: <TeamOutlined />,
    label: "用户管理",
    menuLabel: <NavLink to="/users">用户管理</NavLink>,
    canAccess: (user) => hasPermission(user, "admin.users.view"),
  },
  {
    key: "/roles",
    icon: <SafetyOutlined />,
    label: "角色管理",
    menuLabel: <NavLink to="/roles">角色管理</NavLink>,
    canAccess: (user) => hasPermission(user, "admin.roles.view"),
  },
  {
    key: "/audit-logs",
    icon: <AuditOutlined />,
    label: "审计日志",
    menuLabel: <NavLink to="/audit-logs">审计日志</NavLink>,
    canAccess: (user) => hasPermission(user, "admin.audit.view"),
  },
];

const TAB_STORAGE_KEY = "admin:workspaceTabs";

function sanitizeTabs(rawTabs: WorkspaceTab[]) {
  const deduped: WorkspaceTab[] = [];
  const seen = new Set<string>();
  for (const tab of rawTabs) {
    if (!tab?.path || seen.has(tab.path)) {
      continue;
    }
    seen.add(tab.path);
    deduped.push({ key: tab.path, path: tab.path, label: tab.label || buildTabLabel(tab.path) });
  }
  if (!seen.has("/")) {
    deduped.unshift({ key: "/", path: "/", label: "工作台" });
  }
  return deduped;
}

function buildTabLabel(path: string) {
  if (path === "/") return "工作台";
  if (path === "/skills") return "技能列表";
  if (path.startsWith("/skills/")) return "技能详情";
  if (path.startsWith("/versions/")) return "版本详情";
  if (path.startsWith("/reviews")) return "审核中心";
  if (path.startsWith("/releases")) return "待发布";
  if (path.startsWith("/review-history")) return "处理记录";
  if (path.startsWith("/categories")) return "分类管理";
  if (path.startsWith("/users")) return "用户管理";
  if (path.startsWith("/roles")) return "角色管理";
  if (path.startsWith("/audit-logs")) return "审计日志";
  return "页面";
}

export function AdminLayout({ user, onLogout, loggingOut }: AdminLayoutProps) {
  const location = useLocation();
  const navigate = useNavigate();
  const visibleNavItems = navItems.filter((item) => item.canAccess(user));
  const selectedKey = visibleNavItems
    .map((item) => item.key)
    .find((key) => location.pathname === key || location.pathname.startsWith(`${key}/`))
    ?? "/";
  const canUpload = hasPermission(user, "skill.upload");
  const [persistedTabs, setPersistedTabs] = useState<WorkspaceTab[]>(() => {
    try {
      const raw = window.localStorage.getItem(TAB_STORAGE_KEY);
      if (!raw) return [{ key: "/", path: "/", label: "工作台" }];
      const parsed = JSON.parse(raw) as WorkspaceTab[];
      return Array.isArray(parsed) ? sanitizeTabs(parsed) : [{ key: "/", path: "/", label: "工作台" }];
    } catch {
      return [{ key: "/", path: "/", label: "工作台" }];
    }
  });
  const activePath = `${location.pathname}${location.search ?? ""}`;

  // 路由变化时把当前 path 追加进 tab 列表。仅 useMemo 派生而不写回 state 时，persistedTabs 会停留在旧快照，连续打开多页会「覆盖」掉中间的页签。
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- 将当前路由同步进已打开 tab 列表（无法用纯派生替代）
    setPersistedTabs((prev) => {
      if (prev.some((item) => item.path === activePath)) {
        return prev;
      }
      return sanitizeTabs([
        ...prev,
        { key: activePath, path: activePath, label: buildTabLabel(location.pathname) },
      ]);
    });
  }, [activePath, location.pathname]);

  useEffect(() => {
    window.localStorage.setItem(TAB_STORAGE_KEY, JSON.stringify(persistedTabs));
  }, [persistedTabs]);

  const tabItems = useMemo(
    () =>
      persistedTabs.map((item) => ({
        key: item.key,
        label: item.label,
        closable: item.path !== "/",
      })),
    [persistedTabs],
  );

  return (
    <Layout className="admin-shell">
      <Layout.Sider theme="light" width={240} className="admin-sider">
        <Typography.Title level={4}>Skill Hub Admin</Typography.Title>
        <Menu
          mode="inline"
          selectedKeys={[selectedKey]}
          items={visibleNavItems.map((item) => ({ key: item.key, icon: item.icon, label: item.menuLabel }))}
          className="admin-menu"
        />
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
        <div className="admin-workspace-tabs" id="admin-workspace-tabs">
          <Tabs
            type="editable-card"
            hideAdd
            size="small"
            activeKey={persistedTabs.some((item) => item.path === activePath) ? activePath : tabItems[0]?.key}
            items={tabItems}
            onChange={(key) => navigate(key)}
            onEdit={(targetKey, action) => {
              if (action !== "remove") return;
              const removeKey = String(targetKey);
              setPersistedTabs((prev) => {
                const next = sanitizeTabs(prev.filter((item) => item.key !== removeKey));
                if (!next.length) {
                  navigate("/");
                  return [{ key: "/", path: "/", label: "工作台" }];
                }
                if (removeKey === activePath) {
                  navigate(next[next.length - 1].path);
                }
                return next;
              });
            }}
          />
        </div>
        <Layout.Content className="admin-content">
          <Outlet />
        </Layout.Content>
      </Layout>
    </Layout>
  );
}
