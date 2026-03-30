/**
 * 组件约定：
 * - 承载前台顶部品牌、导航、登录和上传入口，不直接处理会话请求。
 * - 上传入口是否可用由外层 `canUpload` 和回调决定，避免头部自行推断权限逻辑。
 */
import { Button, Layout, Space, Typography } from "antd";
import { Link } from "react-router-dom";

import type { PortalUser } from "../lib/portalTypes";

export function PortalHeader({
  user,
  canUpload,
  onUpload,
  onLoginToggle,
  onLogout,
}: {
  user: PortalUser | null;
  canUpload: boolean;
  onUpload: () => void;
  onLoginToggle: () => void;
  onLogout: () => void;
}) {
  return (
    <Layout.Header className="site-header">
      <Link to="/categories" className="site-brand">
        <div className="brand-mark">S</div>
        <div className="brand-copy">
          <div className="brand-name-row">
            <span className="brand-name">Skill Hub</span>
            <span className="brand-divider" />
            <span className="brand-tagline">企业技能资产广场</span>
          </div>
          <div className="brand-subtitle">上传、审批、发布与版本治理统一在一个技能广场里完成</div>
        </div>
      </Link>
      <nav className="site-nav">
        <Link to="/categories#marketplace-section">技能广场</Link>
        <Link to="/categories#overview-section">平台概览</Link>
      </nav>
      <Space size={12}>
        <Button className="portal-primary-button header-upload-button" type="primary" onClick={onUpload}>
          {canUpload ? "我要上传" : "进入上传通道"}
        </Button>
        {user ? <Typography.Text className="header-user">{user.display_name}</Typography.Text> : null}
        <Button className="portal-secondary-button header-login-button" onClick={user ? onLogout : onLoginToggle}>
          {user ? "退出登录" : "登录收藏"}
        </Button>
      </Space>
    </Layout.Header>
  );
}
