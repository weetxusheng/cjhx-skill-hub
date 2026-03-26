import { useEffect } from "react";
import { Spin } from "antd";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Navigate, Route, Routes, useLocation } from "react-router-dom";

import { apiRequest } from "./lib/api";
import { AdminLayout } from "./components/AdminLayout";
import { LoginPage } from "./pages/LoginPage";
import { AuditLogsPage } from "./pages/AuditLogsPage";
import { CategoriesPage } from "./pages/CategoriesPage";
import { DashboardPage } from "./pages/DashboardPage";
import { ReleasesPage } from "./pages/ReleasesPage";
import { RolesPage } from "./pages/RolesPage";
import { ReviewHistoryPage } from "./pages/ReviewHistoryPage";
import { ReviewsPage } from "./pages/ReviewsPage";
import { SkillDetailPage } from "./pages/SkillDetailPage";
import { SkillsPage } from "./pages/SkillsPage";
import { UsersPage } from "./pages/UsersPage";
import { VersionDetailPage } from "./pages/VersionDetailPage";
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

function firstAllowedPath(user: MeResponse) {
  if (hasPermission(user, "admin.dashboard.view")) return "/";
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
  if (path === "/") return hasPermission(user, "admin.dashboard.view");
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
  const { accessToken, setSession, refreshToken, clearSession } = useAuthStore();

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
      clearSession();
    }
  }, [clearSession, meQuery.isError]);

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
