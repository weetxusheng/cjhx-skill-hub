import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Alert, Button, Drawer, Form, Input, Layout, Typography } from "antd";
import { useEffect, useRef, useState } from "react";
import { Navigate, Route, Routes, useLocation, useSearchParams } from "react-router-dom";

import { apiRequest } from "./lib/api";
import { hasPermission } from "./lib/portalPermissions";
import type { LoginResponse } from "./lib/portalTypes";
import { PortalHeader } from "./components/PortalHeader";
import { PortalUploadCenterDrawer } from "./components/PortalUploadCenterDrawer";
import MarketplacePage from "./pages/MarketplacePage";
import SkillDetailRedirect from "./pages/SkillDetailRedirect";
import { usePortalAuthStore } from "./store/auth";

/**
 * 交互约定：
 * - 加载态：各子路由页面自行处理；单点登录进行中顶栏下提示最多展示约 5 秒后自动收起。
 * - 错误态：登录抽屉内展示接口错误；单点失败在内容区顶部 Alert。
 * - 权限不足态：无 skill 能力时上传入口引导登录或说明（由 Header/抽屉承担）。
 * - 空态：市场页等由子页面处理。
 * - 主系统 SSO：URL 带 `loginname`+`sign` 时自动 POST `/auth/sso-portal`，成功后 replace 去掉查询参数并写入会话。
 */
export default function App() {
  const queryClient = useQueryClient();
  const location = useLocation();
  const [searchParams, setSearchParams] = useSearchParams();
  const { accessToken, user, setSession, clearSession } = usePortalAuthStore();
  const [loginOpen, setLoginOpen] = useState(false);
  const [uploadCenterOpen, setUploadCenterOpen] = useState(false);
  const [ssoError, setSsoError] = useState<string | null>(null);
  /** 单点进行中提示最多展示 5 秒，超时后隐藏文案（请求仍可在后台完成）。 */
  const [ssoLoadingBannerDismissed, setSsoLoadingBannerDismissed] = useState(false);
  const ssoLoadingTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const ssoAttemptStartedRef = useRef(false);
  const canUpload = hasPermission(user, "skill.upload");

  // 账号密码登录是前台点赞、收藏、下载记录和投稿入口的统一会话入口。
  const loginMutation = useMutation({
    mutationFn: (payload: { username: string; password: string }) =>
      apiRequest<LoginResponse>("/auth/login", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    onSuccess: async (payload) => {
      setSession({
        accessToken: payload.access_token,
        refreshToken: payload.refresh_token,
        user: payload.user,
      });
      setLoginOpen(false);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["public-skill-detail"] }),
        queryClient.invalidateQueries({ queryKey: ["public-skills"] }),
      ]);
    },
  });

  // 主系统 SSO 仅负责接管 portal 会话，不额外决定业务跳转，由当前路由自行恢复上下文。
  const ssoMutation = useMutation({
    mutationFn: (payload: { loginname: string; sign: string }) =>
      apiRequest<LoginResponse>("/auth/sso-portal", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    onMutate: () => {
      setSsoLoadingBannerDismissed(false);
    },
    onSuccess: async (payload) => {
      setSsoError(null);
      setSession({
        accessToken: payload.access_token,
        refreshToken: payload.refresh_token,
        user: payload.user,
      });
      const next = new URLSearchParams(searchParams);
      next.delete("loginname");
      next.delete("loginName");
      next.delete("sign");
      next.delete("ycOrderId");
      setSearchParams(next, { replace: true });
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["public-skill-detail"] }),
        queryClient.invalidateQueries({ queryKey: ["public-skills"] }),
      ]);
    },
    onError: (err: Error) => {
      setSsoError(err.message ?? "单点登录失败");
      const next = new URLSearchParams(searchParams);
      next.delete("loginname");
      next.delete("loginName");
      next.delete("sign");
      next.delete("ycOrderId");
      setSearchParams(next, { replace: true });
    },
  });

  const { mutate: mutateSso } = ssoMutation;
  useEffect(() => {
    const ln = searchParams.get("loginname") ?? searchParams.get("loginName");
    const sig = searchParams.get("sign");
    if (!ln || !sig) {
      ssoAttemptStartedRef.current = false;
      return;
    }
    if (ssoAttemptStartedRef.current) {
      return;
    }
    ssoAttemptStartedRef.current = true;
    mutateSso({ loginname: ln, sign: sig });
  }, [searchParams, mutateSso]);

  useEffect(() => {
    if (!ssoMutation.isPending) {
      if (ssoLoadingTimerRef.current !== null) {
        clearTimeout(ssoLoadingTimerRef.current);
        ssoLoadingTimerRef.current = null;
      }
      return;
    }
    ssoLoadingTimerRef.current = setTimeout(() => {
      setSsoLoadingBannerDismissed(true);
      ssoLoadingTimerRef.current = null;
    }, 5000);
    return () => {
      if (ssoLoadingTimerRef.current !== null) {
        clearTimeout(ssoLoadingTimerRef.current);
        ssoLoadingTimerRef.current = null;
      }
    };
  }, [ssoMutation.isPending]);

  useEffect(() => {
    if (!location.hash) {
      return;
    }

    let attempts = 0;
    let timerId: ReturnType<typeof setTimeout> | null = null;
    const targetId = decodeURIComponent(location.hash.slice(1));

    const scrollToHashTarget = () => {
      const target = document.getElementById(targetId);
      if (!target) {
        attempts += 1;
        if (attempts < 8) {
          timerId = setTimeout(scrollToHashTarget, 60);
        }
        return;
      }
      const header = document.querySelector(".site-header");
      const headerOffset = header instanceof HTMLElement ? header.offsetHeight + 12 : 12;
      const top = window.scrollY + target.getBoundingClientRect().top - headerOffset;
      window.scrollTo({ top: Math.max(top, 0), behavior: "smooth" });
    };

    timerId = setTimeout(scrollToHashTarget, 0);
    return () => {
      if (timerId !== null) {
        clearTimeout(timerId);
      }
    };
  }, [location.hash, location.pathname]);

  // “我要上传”优先留在前台：未登录先拉起登录抽屉，已登录直接进入上传中心。
  const handlePortalUploadEntry = () => {
    if (!user) {
      setLoginOpen(true);
      return;
    }
    setUploadCenterOpen(true);
  };

  return (
    <Layout className="page-shell">
      <PortalHeader
        user={user}
        canUpload={canUpload}
        onUpload={handlePortalUploadEntry}
        onLoginToggle={() => setLoginOpen(true)}
        onLogout={clearSession}
      />

      <Layout.Content className="page-content">
        {ssoError ? (
          <Alert type="error" showIcon closable onClose={() => setSsoError(null)} message="单点登录失败" description={ssoError} style={{ marginBottom: 16 }} />
        ) : null}
        {ssoMutation.isPending && !ssoLoadingBannerDismissed ? (
          <Alert type="info" showIcon message="正在通过主系统单点登录…" style={{ marginBottom: 16 }} />
        ) : null}
        <Routes>
          <Route path="/" element={<Navigate to="/categories" replace />} />
          <Route
            path="/categories"
            element={<MarketplacePage accessToken={accessToken} user={user} onOpenLogin={() => setLoginOpen(true)} onUploadEntry={handlePortalUploadEntry} />}
          />
          <Route path="/skills/:slug" element={<SkillDetailRedirect />} />
          <Route path="*" element={<Navigate to="/categories" replace />} />
        </Routes>
      </Layout.Content>

      <Drawer title="登录后继续" open={loginOpen} onClose={() => setLoginOpen(false)} width={420} className="portal-auth-drawer">
        <Typography.Paragraph>登录后可以点赞、收藏技能、保留下载记录，也可以从前台直接投稿。</Typography.Paragraph>
        <Form layout="vertical" size="large" onFinish={(values) => loginMutation.mutate(values)}>
          <Form.Item label="用户名" name="username" initialValue="admin" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item label="密码" name="password" initialValue="ChangeMe123!" rules={[{ required: true }]}>
            <Input.Password />
          </Form.Item>
          {loginMutation.error ? <Alert type="error" showIcon message={(loginMutation.error as Error).message} /> : null}
          <Button className="portal-primary-button auth-submit-button" type="primary" htmlType="submit" block loading={loginMutation.isPending}>
            登录
          </Button>
        </Form>
        {user ? (
          <Button className="portal-secondary-button" style={{ marginTop: 12 }} block onClick={clearSession}>
            切换账号
          </Button>
        ) : null}
      </Drawer>

      <PortalUploadCenterDrawer
        accessToken={accessToken}
        canUpload={canUpload}
        open={uploadCenterOpen}
        onClose={() => setUploadCenterOpen(false)}
      />
    </Layout>
  );
}
