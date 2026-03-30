import { useEffect, useRef } from "react";
import { Spin } from "antd";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom";

import { apiRequest } from "./lib/api";
import { AdminLayout } from "./components/AdminLayout";
import { LoginPage } from "./pages/auth/LoginPage";
import { AuditLogsPage } from "./pages/governance/AuditLogsPage";
import { CategoriesPage } from "./pages/governance/CategoriesPage";
import { DashboardPage } from "./pages/workbench/DashboardPage";
import { ReleasesPage } from "./pages/workbench/ReleasesPage";
import { RolesPage } from "./pages/governance/RolesPage";
import { ReviewHistoryPage } from "./pages/workbench/ReviewHistoryPage";
import { ReviewsPage } from "./pages/workbench/ReviewsPage";
import { SkillDetailPage } from "./pages/detail/SkillDetailPage";
import { SkillsPage } from "./pages/workbench/SkillsPage";
import { UsersPage } from "./pages/governance/UsersPage";
import { VersionDetailPage } from "./pages/detail/VersionDetailPage";
import { hasPermission } from "./lib/permissions";
import { useAuthStore } from "./store/auth";

type MeResponse = {
  id: string;
  username: string;
  display_name: string;
  email: string | null;
  status: "active" | "disabled";
  roles: string[];
  permissions: string[];
  last_login_at: string | null;
};

const ADMIN_LAST_PATH_STORAGE_KEY = "admin:lastPath";
const ADMIN_TAB_STORAGE_KEY = "admin:workspaceTabs";

function clearAdminUiStateStorage() {
  window.localStorage.removeItem(ADMIN_LAST_PATH_STORAGE_KEY);
  window.localStorage.removeItem(ADMIN_TAB_STORAGE_KEY);
}

function canAccessWorkbench(user: MeResponse) {
  return (
    hasPermission(user, "admin.dashboard.view")
    || hasPermission(user, "skill.view")
    || hasPermission(user, "skill.review")
    || hasPermission(user, "skill.publish")
  );
}

function firstAllowedPath(user: MeResponse) {
  if (canAccessWorkbench(user)) return "/";
  if (hasPermission(user, "skill.view")) return "/skills";
  if (hasPermission(user, "skill.review")) return "/reviews";
  if (hasPermission(user, "skill.publish")) return "/releases";
  if (hasPermission(user, "skill.view")) return "/review-history";
  if (hasPermission(user, "admin.categories.view")) return "/categories";
  if (hasPermission(user, "admin.users.view")) return "/users";
  if (hasPermission(user, "admin.roles.view")) return "/roles";
  if (hasPermission(user, "admin.audit.view")) return "/audit-logs";
  return "/login";
}

function canAccessPath(user: MeResponse, path: string) {
  if (path === "/") return canAccessWorkbench(user);
  if (path === "/skills" || path.startsWith("/skills/") || path.startsWith("/versions/")) return hasPermission(user, "skill.view");
  if (path.startsWith("/reviews")) return hasPermission(user, "skill.review");
  if (path.startsWith("/releases")) return hasPermission(user, "skill.publish");
  if (path.startsWith("/review-history")) return hasPermission(user, "skill.view");
  if (path.startsWith("/categories")) return hasPermission(user, "admin.categories.view");
  if (path.startsWith("/users")) return hasPermission(user, "admin.users.view");
  if (path.startsWith("/roles")) return hasPermission(user, "admin.roles.view");
  if (path.startsWith("/audit-logs")) return hasPermission(user, "admin.audit.view");
  return false;
}

function ProtectedApp() {
  const location = useLocation();
  const navigate = useNavigate();
  const { accessToken, setSession, refreshToken, clearSession } = useAuthStore();
  const hasRestoredLastPathRef = useRef(false);

  const meQuery = useQuery({
    queryKey: ["me", accessToken],
    enabled: Boolean(accessToken),
    queryFn: () => apiRequest<MeResponse>("/auth/me", { token: accessToken }),
  });

  useEffect(() => {
    if (refreshToken && meQuery.data && accessToken) {
      setSession({ accessToken, refreshToken, user: meQuery.data });
    }
  }, [accessToken, meQuery.data, refreshToken, setSession]);

  useEffect(() => {
    if (meQuery.isError) {
      clearAdminUiStateStorage();
      clearSession();
    }
  }, [clearSession, meQuery.isError]);

  // Persist last visited admin route (for refresh / re-login)
  // Must be declared before any early return to keep hooks order stable.
  useEffect(() => {
    if (!accessToken) {
      return;
    }
    if (!meQuery.data) {
      return;
    }
    const pathWithSearch = `${location.pathname}${location.search ?? ""}`;
    if (pathWithSearch && pathWithSearch !== "/login") {
      window.localStorage.setItem(ADMIN_LAST_PATH_STORAGE_KEY, pathWithSearch);
    }
  }, [accessToken, meQuery.data, location.pathname, location.search]);

  useEffect(() => {
    if (!meQuery.data || location.pathname !== "/" || hasRestoredLastPathRef.current) {
      return;
    }

    hasRestoredLastPathRef.current = true;
    const savedPath = window.localStorage.getItem(ADMIN_LAST_PATH_STORAGE_KEY);
    if (savedPath && savedPath !== "/" && canAccessPath(meQuery.data, savedPath)) {
      navigate(savedPath, { replace: true });
    }
  }, [location.pathname, meQuery.data, navigate]);

  const logoutMutation = useMutation({
    mutationFn: async () => {
      if (!refreshToken || !accessToken) {
        return;
      }
      await apiRequest("/auth/logout", {
        method: "POST",
        token: accessToken,
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
    },
    onSettled: () => {
      clearAdminUiStateStorage();
      clearSession();
    },
  });

  if (!accessToken) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  if (meQuery.isLoading) {
    return (
      <div className="center-shell">
        <Spin size="large" />
      </div>
    );
  }

  if (meQuery.isError || !meQuery.data) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  if (!canAccessPath(meQuery.data, location.pathname)) {
    return <Navigate to={firstAllowedPath(meQuery.data)} replace />;
  }

  return (
    <AdminLayout user={meQuery.data} onLogout={() => logoutMutation.mutate()} loggingOut={logoutMutation.isPending} />
  );
}

/**
 * 交互约定：
 * - 加载态：会话校验期间展示全屏 Spin，不提前渲染后台骨架。
 * - 错误态：`/auth/me` 失败时清理本地会话并回到登录页。
 * - 权限不足态：根据用户 capability 自动导航到首个允许页面，禁止空白后台。
 * - 上下文恢复：登录后优先恢复最近一次后台访问路径，恢复失败再回默认工作台。
 */
export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<ProtectedApp />}>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/skills" element={<SkillsPage />} />
        <Route path="/skills/:skillId" element={<SkillDetailPage />} />
        <Route path="/versions/:versionId" element={<VersionDetailPage />} />
        <Route path="/reviews" element={<ReviewsPage />} />
        <Route path="/releases" element={<ReleasesPage />} />
        <Route path="/review-history" element={<ReviewHistoryPage />} />
        <Route path="/categories" element={<CategoriesPage />} />
        <Route path="/users" element={<UsersPage />} />
        <Route path="/roles" element={<RolesPage />} />
        <Route path="/audit-logs" element={<AuditLogsPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
