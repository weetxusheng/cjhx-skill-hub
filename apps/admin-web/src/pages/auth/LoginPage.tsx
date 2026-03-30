import { Button, Card, Form, Input, Typography } from "antd";
import { useMutation } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";

import { apiRequest } from "../../lib/api";
import { useAuthStore } from "../../store/auth";

type LoginResponse = {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
  user: {
    id: string;
    username: string;
    display_name: string;
    email: string | null;
    status: "active" | "disabled";
    roles: string[];
    permissions: string[];
    last_login_at: string | null;
  };
};

export function LoginPage() {
  /**
   * 交互约定：
   * - 加载中：禁用表单并显示按钮加载态
   * - 错误：展示明确错误信息（不允许静默失败）
   * - 成功：持久化会话 token 并跳转首页
   */
  const navigate = useNavigate();
  const setSession = useAuthStore((state) => state.setSession);

  const loginMutation = useMutation({
    mutationFn: (payload: { username: string; password: string }) =>
      apiRequest<LoginResponse>("/auth/login", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    onSuccess: (data) => {
      setSession({
        accessToken: data.access_token,
        refreshToken: data.refresh_token,
        user: data.user,
      });
      navigate("/", { replace: true });
    },
  });

  return (
    <div className="login-shell">
      <Card className="login-card" variant="borderless">
        <Typography.Text className="login-eyebrow">Skill Hub 管理后台</Typography.Text>
        <Typography.Paragraph className="login-hint">
          当前首版已接通真实认证接口。初始化管理员账号为 `admin`，密码为 `ChangeMe123!`。
        </Typography.Paragraph>

        <Form
          layout="vertical"
          size="large"
          onFinish={(values) => loginMutation.mutate(values)}
          disabled={loginMutation.isPending}
        >
          <Form.Item label="用户名" name="username" initialValue="admin" rules={[{ required: true, message: "请输入用户名" }]}>
            <Input placeholder="请输入用户名" />
          </Form.Item>
          <Form.Item label="密码" name="password" initialValue="ChangeMe123!" rules={[{ required: true, message: "请输入密码" }]}>
            <Input.Password placeholder="请输入密码" />
          </Form.Item>

          {loginMutation.error ? <Typography.Text type="danger">{(loginMutation.error as Error).message}</Typography.Text> : null}

          <Button type="primary" htmlType="submit" block loading={loginMutation.isPending}>
            登录
          </Button>
        </Form>
      </Card>
    </div>
  );
}

