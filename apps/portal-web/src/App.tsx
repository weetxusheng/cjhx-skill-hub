import { useDeferredValue, useEffect, useMemo, useState, type CSSProperties } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AppstoreOutlined,
  ArrowRightOutlined,
  CheckCircleFilled,
  CodeSandboxOutlined,
  CopyOutlined,
  DownloadOutlined,
  FireOutlined,
  LikeFilled,
  LikeOutlined,
  RobotOutlined,
  SearchOutlined,
  StarOutlined,
  ThunderboltOutlined,
  UserOutlined,
} from "@ant-design/icons";
import {
  Alert,
  Button,
  Card,
  Empty,
  Form,
  Input,
  Layout,
  message,
  Modal,
  Pagination,
  Select,
  Space,
  Spin,
  Tag,
  Tabs,
  Typography,
  Upload,
  Drawer,
} from "antd";
import type { UploadFile } from "antd/es/upload/interface";
import dayjs from "dayjs";
import { Link, Navigate, Route, Routes, useParams, useSearchParams } from "react-router-dom";

import { ADMIN_WEB_URL, API_BASE_URL, apiRequest } from "./lib/api";
import { usePortalAuthStore } from "./store/auth";

type CategoryItem = {
  id: string;
  name: string;
  slug: string;
  icon: string | null;
  description: string | null;
  sort_order: number;
  is_visible: boolean;
  skill_count: number;
};

type PublicSkillListItem = {
  id: string;
  name: string;
  slug: string;
  summary: string;
  category_name: string;
  category_slug: string;
  latest_version_no: string | null;
  download_count: number;
  favorite_count: number;
  like_count: number;
  published_at: string | null;
  icon_file_id: string | null;
};

type PagedResponse<T> = {
  items: T[];
  total: number;
  page: number;
  page_size: number;
};

type PublicSkillDetailResponse = {
  skill: {
    id: string;
    name: string;
    slug: string;
    summary: string;
    description: string;
    category_name: string;
    category_slug: string;
    latest_version_no: string | null;
    download_count: number;
    favorite_count: number;
    like_count: number;
    published_at: string | null;
  };
  current_version: {
    id: string;
    version: string;
    readme_markdown: string;
    readme_html: string;
    changelog: string;
    install_notes: string;
    breaking_changes: string;
    published_at: string | null;
  };
  published_versions: Array<{
    id: string;
    version: string;
    review_status: string;
    created_at: string;
    published_at: string | null;
  }>;
  is_favorited: boolean;
  is_liked: boolean;
  usage_guide: {
    agent: {
      standard_prompt: string;
      accelerated_prompt: string;
    };
    human: {
      standard_command: string;
      accelerated_command: string;
      post_install_command: string;
    };
  };
};

type UsageGuideValue = {
  agent: {
    standard_prompt: string;
    accelerated_prompt: string;
  };
  human: {
    standard_command: string;
    accelerated_command: string;
    post_install_command: string;
  };
};

type PortalUser = {
  id: string;
  username: string;
  display_name: string;
  email: string | null;
  status: "active" | "disabled";
  roles: string[];
  permissions: string[];
};

type LoginResponse = {
  access_token: string;
  refresh_token: string;
  user: PortalUser;
};

type CategoryVisual = {
  color: string;
  background: string;
  border: string;
  paths: string[];
};

const CATEGORY_VISUALS: Record<string, CategoryVisual> = {
  "ai-intelligence": {
    color: "#007AFF",
    background: "rgba(0, 122, 255, 0.10)",
    border: "rgba(0, 122, 255, 0.133)",
    paths: [
      "M12 5a3 3 0 1 0-5.997.125 4 4 0 0 0-2.526 5.77 4 4 0 0 0 .556 6.588A4 4 0 1 0 12 18Z",
      "M12 5a3 3 0 1 1 5.997.125 4 4 0 0 1 2.526 5.77 4 4 0 0 1-.556 6.588A4 4 0 1 1 12 18Z",
      "M15 13a4.5 4.5 0 0 1-3-4 4.5 4.5 0 0 1-3 4",
      "M17.599 6.5a3 3 0 0 0 .399-1.375",
      "M6.003 5.125A3 3 0 0 0 6.401 6.5",
      "M3.477 10.896a4 4 0 0 1 .585-.396",
      "M19.938 10.5a4 4 0 0 1 .585.396",
      "M6 18a4 4 0 0 1-1.967-.516",
      "M19.967 17.484A4 4 0 0 1 18 18",
    ],
  },
  "developer-tools": {
    color: "#5856D6",
    background: "rgba(88, 86, 214, 0.10)",
    border: "rgba(88, 86, 214, 0.133)",
    paths: ["m18 16 4-4-4-4", "m6 8-4 4 4 4", "m14.5 4-5 16"],
  },
  productivity: {
    color: "#34C759",
    background: "rgba(52, 199, 89, 0.10)",
    border: "rgba(52, 199, 89, 0.133)",
    paths: [
      "M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z",
      "m12 15-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z",
      "M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0",
      "M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5",
    ],
  },
  "data-analysis": {
    color: "#FF9500",
    background: "rgba(255, 149, 0, 0.10)",
    border: "rgba(255, 149, 0, 0.133)",
    paths: ["M3 3v16a2 2 0 0 0 2 2h16", "M18 17V9", "M13 17V5", "M8 17v-3"],
  },
  "content-creation": {
    color: "#FF2D55",
    background: "rgba(255, 45, 85, 0.10)",
    border: "rgba(255, 45, 85, 0.133)",
    paths: [
      "M15.707 21.293a1 1 0 0 1-1.414 0l-1.586-1.586a1 1 0 0 1 0-1.414l5.586-5.586a1 1 0 0 1 1.414 0l1.586 1.586a1 1 0 0 1 0 1.414z",
      "m18 13-1.375-6.874a1 1 0 0 0-.746-.776L3.235 2.028a1 1 0 0 0-1.207 1.207L5.35 15.879a1 1 0 0 0 .776.746L13 18",
      "m2.3 2.3 7.286 7.286",
      "M11 11m-2 0a2 2 0 1 0 4 0a2 2 0 1 0 -4 0",
    ],
  },
  "security-compliance": {
    color: "#32ADE6",
    background: "rgba(50, 173, 230, 0.10)",
    border: "rgba(50, 173, 230, 0.133)",
    paths: ["M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"],
  },
  "communication-collaboration": {
    color: "#30D158",
    background: "rgba(48, 209, 88, 0.10)",
    border: "rgba(48, 209, 88, 0.133)",
    paths: ["M7.9 20A9 9 0 1 0 4 16.1L2 22Z"],
  },
};

const CATEGORY_VISUALS_BY_NAME: Record<string, string> = {
  "AI 智能": "ai-intelligence",
  开发工具: "developer-tools",
  效率提升: "productivity",
  数据分析: "data-analysis",
  内容创作: "content-creation",
  安全合规: "security-compliance",
  通讯协作: "communication-collaboration",
};

function hasPermission(user: PortalUser | null, permission: string) {
  return Boolean(user?.permissions?.includes(permission));
}

function buildFallbackUsageGuide(detail: PublicSkillDetailResponse): UsageGuideValue {
  const downloadUrl = `${API_BASE_URL}/public/skills/${detail.skill.id}/download`;
  const installNotes = detail.current_version.install_notes || "按 README 指引完成安装与配置。";
  return {
    agent: {
      standard_prompt: `请帮我使用 Skill Hub 技能“${detail.skill.name}”（slug: ${detail.skill.slug}）。先通过 ${downloadUrl} 下载当前已发布版本，阅读 README 和安装说明，然后按技能用途执行。`,
      accelerated_prompt: `请优先使用 Skill Hub 平台接口下载技能“${detail.skill.name}”（slug: ${detail.skill.slug}），固定使用当前 published 版本；下载地址为 ${downloadUrl}。下载后先阅读 README，再根据安装说明执行。`,
    },
    human: {
      standard_command: `curl -L "${downloadUrl}" -o "${detail.skill.slug}.zip"`,
      accelerated_command: `curl --retry 3 --retry-delay 2 -L "${downloadUrl}" -o "${detail.skill.slug}.zip"`,
      post_install_command: `unzip -o "${detail.skill.slug}.zip" -d "./${detail.skill.slug}" && cd "./${detail.skill.slug}" && printf "%s\\n" "${installNotes}"`,
    },
  };
}

function resolveUsageGuide(detail: PublicSkillDetailResponse): UsageGuideValue {
  const usageGuide = detail.usage_guide;
  if (
    usageGuide &&
    usageGuide.agent &&
    usageGuide.human &&
    typeof usageGuide.agent.standard_prompt === "string" &&
    typeof usageGuide.agent.accelerated_prompt === "string" &&
    typeof usageGuide.human.standard_command === "string" &&
    typeof usageGuide.human.accelerated_command === "string" &&
    typeof usageGuide.human.post_install_command === "string"
  ) {
    return usageGuide;
  }
  return buildFallbackUsageGuide(detail);
}

function getCategoryVisual(category: Pick<CategoryItem | PublicSkillListItem, "name" | "slug"> | { category_name: string; category_slug: string }) {
  const slug = "slug" in category ? category.slug : category.category_slug;
  const name = "name" in category ? category.name : category.category_name;
  return CATEGORY_VISUALS[slug] ?? CATEGORY_VISUALS[CATEGORY_VISUALS_BY_NAME[name]] ?? CATEGORY_VISUALS.productivity;
}

function CategoryIcon({
  category,
  className,
}: {
  category: Pick<CategoryItem | PublicSkillListItem, "name" | "slug"> | { category_name: string; category_slug: string };
  className?: string;
}) {
  const visual = getCategoryVisual(category);
  return (
    <span
      className={className ?? "category-icon"}
      style={
        {
          "--icon-color": visual.color,
          "--icon-bg": visual.background,
          "--icon-border": visual.border,
        } as CSSProperties
      }
    >
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        {visual.paths.map((path) => (
          <path key={path} d={path} />
        ))}
      </svg>
    </span>
  );
}

function SkillCard({
  skill,
  onOpen,
}: {
  skill: PublicSkillListItem;
  onOpen: (slug: string) => void;
}) {
  return (
    <Card key={skill.id} className="skill-card" variant="borderless" hoverable onClick={() => onOpen(skill.slug)}>
      <div className="skill-card-topline">
        <div className="skill-card-heading">
          <CategoryIcon category={{ name: skill.category_name, slug: skill.category_slug }} className="skill-category-icon" />
          <div>
            <div className="skill-card-category-name">{skill.category_name}</div>
            <div className="skill-card-date">{skill.published_at ? dayjs(skill.published_at).format("YYYY-MM-DD") : "未发布"}</div>
          </div>
        </div>
        <span className="skill-version-pill">v{skill.latest_version_no ?? "-"}</span>
      </div>
      <Typography.Title level={4} className="skill-title">
        {skill.name}
      </Typography.Title>
      <Typography.Paragraph className="skill-summary">{skill.summary}</Typography.Paragraph>
      <div className="skill-stats">
        <span>
          <DownloadOutlined />
          下载 {skill.download_count}
        </span>
        <span>
          <StarOutlined />
          收藏 {skill.favorite_count}
        </span>
        <span>
          <LikeOutlined />
          点赞 {skill.like_count}
        </span>
      </div>
      <Button
        block
        className="portal-secondary-button skill-card-button"
        onClick={(event) => {
          event.stopPropagation();
          onOpen(skill.slug);
        }}
      >
        查看详情
        <ArrowRightOutlined />
      </Button>
    </Card>
  );
}

function PortalHeader({
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
          我要上传
        </Button>
        {user ? <Typography.Text className="header-user">{user.display_name}</Typography.Text> : null}
        <Button className="portal-secondary-button header-login-button" onClick={user ? onLogout : onLoginToggle}>
          {user ? "退出登录" : "登录收藏"}
        </Button>
      </Space>
    </Layout.Header>
  );
}

function UsageGuideSection({
  detail,
  selectedUsageMode,
  setUsageMode,
}: {
  detail: PublicSkillDetailResponse;
  selectedUsageMode: "agent" | "human";
  setUsageMode: (mode: "agent" | "human") => void;
}) {
  const usageGuide = resolveUsageGuide(detail);
  const copyText = async (value: string, label: string) => {
    await navigator.clipboard.writeText(value);
    message.success(`${label}已复制`);
  };

  return (
    <Card title="安装方式" className="drawer-card">
      <Tabs
        activeKey={selectedUsageMode}
        onChange={(value) => setUsageMode(value as "agent" | "human")}
        items={[
          {
            key: "agent",
            label: (
              <span className="usage-tab-label">
                <RobotOutlined />
                我是 Agent
              </span>
            ),
            children: (
              <div className="usage-guide-grid">
                <div className="usage-guide-card">
                  <div className="usage-guide-card-head">
                    <div>
                      <strong>标准平台指引</strong>
                      <p>复制给你的 Agent，让它按平台发布版本去下载并使用这个 Skill。</p>
                    </div>
                    <Button
                      className="portal-secondary-button usage-copy-button"
                      icon={<CopyOutlined />}
                      onClick={() => copyText(usageGuide.agent.standard_prompt, "Agent 标准提示词")}
                    >
                      复制
                    </Button>
                  </div>
                  <pre className="usage-guide-code">{usageGuide.agent.standard_prompt}</pre>
                </div>
                <div className="usage-guide-card">
                  <div className="usage-guide-card-head">
                    <div>
                      <strong>优先使用平台链路</strong>
                      <p>适合希望 Agent 明确走平台下载接口、优先使用当前发布版本的场景。</p>
                    </div>
                    <Button
                      className="portal-secondary-button usage-copy-button"
                      icon={<ThunderboltOutlined />}
                      onClick={() => copyText(usageGuide.agent.accelerated_prompt, "Agent 加速提示词")}
                    >
                      复制
                    </Button>
                  </div>
                  <pre className="usage-guide-code">{usageGuide.agent.accelerated_prompt}</pre>
                </div>
              </div>
            ),
          },
          {
            key: "human",
            label: (
              <span className="usage-tab-label">
                <UserOutlined />
                我是 Human
              </span>
            ),
            children: (
              <div className="usage-guide-grid">
                <div className="usage-guide-card">
                  <div className="usage-guide-card-head">
                    <div>
                      <strong>标准下载命令</strong>
                      <p>下载当前已发布 ZIP 包并落到本地。</p>
                    </div>
                    <Button
                      className="portal-secondary-button usage-copy-button"
                      icon={<CopyOutlined />}
                      onClick={() => copyText(usageGuide.human.standard_command, "标准下载命令")}
                    >
                      复制
                    </Button>
                  </div>
                  <pre className="usage-guide-code">{usageGuide.human.standard_command}</pre>
                </div>
                <div className="usage-guide-card">
                  <div className="usage-guide-card-head">
                    <div>
                      <strong>加速下载命令</strong>
                      <p>更适合需要重试或网络不稳定时使用。</p>
                    </div>
                    <Button
                      className="portal-secondary-button usage-copy-button"
                      icon={<ThunderboltOutlined />}
                      onClick={() => copyText(usageGuide.human.accelerated_command, "加速下载命令")}
                    >
                      复制
                    </Button>
                  </div>
                  <pre className="usage-guide-code">{usageGuide.human.accelerated_command}</pre>
                </div>
                <div className="usage-guide-card">
                  <div className="usage-guide-card-head">
                    <div>
                      <strong>安装后建议操作</strong>
                      <p>下载后直接执行这段命令，解压并阅读 README。</p>
                    </div>
                    <Button
                      className="portal-secondary-button usage-copy-button"
                      icon={<CopyOutlined />}
                      onClick={() => copyText(usageGuide.human.post_install_command, "安装后命令")}
                    >
                      复制
                    </Button>
                  </div>
                  <pre className="usage-guide-code">{usageGuide.human.post_install_command}</pre>
                </div>
              </div>
            ),
          },
        ]}
      />
    </Card>
  );
}

function SkillDetailContent({
  detail,
  accessToken,
  selectedUsageMode,
  setUsageMode,
  onOpenLogin,
}: {
  detail: PublicSkillDetailResponse;
  accessToken: string | null;
  selectedUsageMode: "agent" | "human";
  setUsageMode: (mode: "agent" | "human") => void;
  onOpenLogin: () => void;
}) {
  const queryClient = useQueryClient();

  const favoriteMutation = useMutation({
    mutationFn: async (favorited: boolean) =>
      apiRequest(`/public/skills/${detail.skill.id}/favorite`, {
        method: favorited ? "DELETE" : "POST",
        token: accessToken ?? undefined,
      }),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["public-skills"] }),
        queryClient.invalidateQueries({ queryKey: ["public-skill-detail", detail.skill.slug] }),
      ]);
    },
  });

  const likeMutation = useMutation({
    mutationFn: async (liked: boolean) =>
      apiRequest(`/public/skills/${detail.skill.id}/like`, {
        method: liked ? "DELETE" : "POST",
        token: accessToken ?? undefined,
      }),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["public-skills"] }),
        queryClient.invalidateQueries({ queryKey: ["public-skill-detail", detail.skill.slug] }),
      ]);
    },
  });

  const downloadMutation = useMutation({
    mutationFn: async () => {
      const response = await fetch(`${API_BASE_URL}/public/skills/${detail.skill.id}/download`, {
        headers: accessToken ? { Authorization: `Bearer ${accessToken}` } : {},
      });
      if (!response.ok) {
        const payload = await response.json().catch(() => ({ detail: "下载失败" }));
        throw new Error(payload.detail ?? payload.message ?? "下载失败");
      }
      const blob = await response.blob();
      const downloadUrl = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      const disposition = response.headers.get("content-disposition");
      const filename = disposition?.match(/filename=\"?([^\"]+)\"?/)?.[1] ?? `${detail.skill.slug}.zip`;
      anchor.href = downloadUrl;
      anchor.download = filename;
      anchor.click();
      URL.revokeObjectURL(downloadUrl);
    },
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["public-skills"] }),
        queryClient.invalidateQueries({ queryKey: ["public-skill-detail", detail.skill.slug] }),
      ]);
    },
  });

  return (
    <Space direction="vertical" size={20} style={{ width: "100%" }}>
      <Card variant="borderless" className="drawer-card drawer-hero-card detail-hero-card">
        <div className="drawer-skill-topline">
          <CategoryIcon
            category={{
              category_name: detail.skill.category_name,
              category_slug: detail.skill.category_slug,
            }}
            className="drawer-category-icon"
          />
          <div className="detail-head-copy">
            <Typography.Title level={2} style={{ marginBottom: 8 }}>
              {detail.skill.name}
            </Typography.Title>
            <Space wrap>
              <Tag color="orange">{detail.skill.category_name}</Tag>
              <Tag>{detail.skill.slug}</Tag>
              <Tag>版本 {detail.current_version.version}</Tag>
              <Tag>发布时间 {detail.current_version.published_at ? dayjs(detail.current_version.published_at).format("YYYY-MM-DD HH:mm") : "-"}</Tag>
            </Space>
          </div>
        </div>
        <Typography.Paragraph className="drawer-summary">{detail.skill.summary}</Typography.Paragraph>
        <Typography.Paragraph>{detail.skill.description}</Typography.Paragraph>

        <div className="detail-metric-row">
          <div className="detail-metric-card">
            <span>下载</span>
            <strong>{detail.skill.download_count}</strong>
          </div>
          <div className="detail-metric-card">
            <span>收藏</span>
            <strong>{detail.skill.favorite_count}</strong>
          </div>
          <div className="detail-metric-card">
            <span>点赞</span>
            <strong>{detail.skill.like_count}</strong>
          </div>
        </div>

        <Space wrap className="drawer-actions">
          <Button
            className={detail.is_liked ? "portal-primary-button" : "portal-secondary-button"}
            type={detail.is_liked ? "primary" : "default"}
            icon={detail.is_liked ? <LikeFilled /> : <LikeOutlined />}
            onClick={() => {
              if (!accessToken) {
                onOpenLogin();
                return;
              }
              likeMutation.mutate(detail.is_liked);
            }}
            loading={likeMutation.isPending}
          >
            {detail.is_liked ? "取消点赞" : "点赞"}
          </Button>
          <Button
            className={detail.is_favorited ? "portal-primary-button" : "portal-secondary-button"}
            type={detail.is_favorited ? "primary" : "default"}
            onClick={() => {
              if (!accessToken) {
                onOpenLogin();
                return;
              }
              favoriteMutation.mutate(detail.is_favorited);
            }}
            loading={favoriteMutation.isPending}
          >
            {detail.is_favorited ? "取消收藏" : "收藏"}
          </Button>
          <Button className="portal-primary-button" type="primary" onClick={() => downloadMutation.mutate()} loading={downloadMutation.isPending}>
            下载技能包
          </Button>
        </Space>
      </Card>

      <UsageGuideSection detail={detail} selectedUsageMode={selectedUsageMode} setUsageMode={setUsageMode} />

      <Card title="README" className="drawer-card">
        <div className="markdown-preview" dangerouslySetInnerHTML={{ __html: detail.current_version.readme_html }} />
      </Card>

      <Card title="更新说明" className="drawer-card">
        <Typography.Paragraph>{detail.current_version.changelog || "暂无更新说明"}</Typography.Paragraph>
        <Typography.Paragraph>安装说明：{detail.current_version.install_notes || "暂无安装说明"}</Typography.Paragraph>
        <Typography.Paragraph>破坏性变更：{detail.current_version.breaking_changes || "暂无破坏性变更"}</Typography.Paragraph>
      </Card>

      <Card title="历史发布版本" className="drawer-card">
        <div className="version-list">
          {detail.published_versions.map((item) => (
            <div key={item.id} className="version-item">
              <div>
                <strong>{item.version}</strong>
                <p>已发布版本归档记录</p>
              </div>
              <span>{item.published_at ? dayjs(item.published_at).format("YYYY-MM-DD HH:mm") : "-"}</span>
            </div>
          ))}
        </div>
      </Card>
    </Space>
  );
}

function MarketplacePage({
  accessToken,
  user,
  onOpenLogin,
  onUploadEntry,
}: {
  accessToken: string | null;
  user: PortalUser | null;
  onOpenLogin: () => void;
  onUploadEntry: () => void;
}) {
  const [searchParams, setSearchParams] = useSearchParams();
  const [category, setCategory] = useState<string | undefined>();
  const [searchInput, setSearchInput] = useState("");
  const [sort, setSort] = useState("latest");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(8);
  const deferredSearch = useDeferredValue(searchInput.trim());
  const canUpload = hasPermission(user, "skill.upload");
  const selectedSkillSlug = searchParams.get("skill");
  const selectedUsageMode = searchParams.get("usage") === "human" ? "human" : "agent";

  useEffect(() => {
    setPage(1);
  }, [category, deferredSearch, sort]);

  const categoriesQuery = useQuery({
    queryKey: ["public-categories"],
    queryFn: () => apiRequest<CategoryItem[]>("/public/categories"),
  });

  const skillsQuery = useQuery({
    queryKey: ["public-skills", category, deferredSearch, sort, page, pageSize],
    queryFn: () => {
      const query = new URLSearchParams({
        sort,
        page: String(page),
        page_size: String(pageSize),
      });
      if (category) query.set("category", category);
      if (deferredSearch) query.set("q", deferredSearch);
      return apiRequest<PagedResponse<PublicSkillListItem>>(`/public/skills?${query.toString()}`, { token: accessToken ?? undefined });
    },
  });

  const detailQuery = useQuery({
    queryKey: ["public-skill-detail", selectedSkillSlug, accessToken],
    enabled: Boolean(selectedSkillSlug),
    queryFn: () => apiRequest<PublicSkillDetailResponse>(`/public/skills/${selectedSkillSlug}`, { token: accessToken ?? undefined }),
  });

  const totalPublishedSkills = useMemo(
    () => (categoriesQuery.data ?? []).reduce((sum, item) => sum + item.skill_count, 0),
    [categoriesQuery.data],
  );
  const visibleCategoryCount = categoriesQuery.data?.length ?? 0;
  const selectedCategoryName = category
    ? categoriesQuery.data?.find((item) => item.slug === category)?.name ?? category
    : "全部技能";
  const hasFilters = Boolean(category || deferredSearch);

  const openSkillDetail = (slug: string) => {
    const next = new URLSearchParams(searchParams);
    next.set("skill", slug);
    next.set("usage", "agent");
    setSearchParams(next, { replace: false });
  };

  const closeSkillDetail = () => {
    const next = new URLSearchParams(searchParams);
    next.delete("skill");
    next.delete("usage");
    setSearchParams(next, { replace: false });
  };

  const setUsageMode = (mode: "agent" | "human") => {
    const next = new URLSearchParams(searchParams);
    if (selectedSkillSlug) {
      next.set("skill", selectedSkillSlug);
    }
    next.set("usage", mode);
    setSearchParams(next, { replace: true });
  };

  return (
    <>
      <section className="marketplace-section" id="marketplace-section">
        <div className="marketplace-header">
          <div className="marketplace-copy">
            <div className="hero-kicker">
              <FireOutlined />
              <span>技能广场</span>
            </div>
            <Typography.Title className="marketplace-title">自由探索，创金技能广场</Typography.Title>
            <Typography.Paragraph className="marketplace-copy-text">
              直接进入技能广场，按分类、关键词和热度快速筛选，快速发现可用技能。
            </Typography.Paragraph>
          </div>
          <div className="marketplace-summary-card">
            <div className="summary-stat-grid">
              <div className="summary-stat">
                <span className="summary-stat-icon">
                  <AppstoreOutlined />
                </span>
                <strong>{totalPublishedSkills}</strong>
                <span>已发布技能</span>
              </div>
              <div className="summary-stat">
                <span className="summary-stat-icon">
                  <CodeSandboxOutlined />
                </span>
                <strong>{visibleCategoryCount}</strong>
                <span>开放分类</span>
              </div>
              <div className="summary-stat">
                <span className="summary-stat-icon">
                  <CheckCircleFilled />
                </span>
                <strong>3 步</strong>
                <span>上传到发布</span>
              </div>
            </div>
            <div className="marketplace-summary-note">
              <strong>投稿入口</strong>
              <span>{canUpload ? "当前账号已具备上传权限，可直接从前台提交 ZIP 技能包。" : "登录贡献者或管理员账号后，可直接从前台投稿。"}</span>
            </div>
          </div>
        </div>

        <div className="marketplace-panel">
          <div className="marketplace-toolbar">
            <div className="section-heading">
              <div>
                <Typography.Text className="section-kicker">探索全部技能</Typography.Text>
                <Typography.Title level={2} className="section-title">
                  技能广场
                </Typography.Title>
              </div>
              <Typography.Paragraph className="section-copy">
                当前聚焦 {selectedCategoryName}，支持按真实分类、关键词与热度快速筛选。
              </Typography.Paragraph>
            </div>

            {categoriesQuery.isLoading ? (
              <div className="toolbar-state">
                <Spin />
              </div>
            ) : categoriesQuery.isError ? (
              <Alert type="error" showIcon message={(categoriesQuery.error as Error).message} />
            ) : (
              <div className="marketplace-toolbar-content">
                <div className="category-grid">
                  <button type="button" className={`category-card ${!category ? "category-card-active" : ""}`} onClick={() => setCategory(undefined)}>
                    <span className="category-icon category-icon-all">
                      <AppstoreOutlined />
                    </span>
                    <span className="category-card-name">全部技能</span>
                    <strong>{totalPublishedSkills}</strong>
                  </button>
                  {(categoriesQuery.data ?? []).map((item) => (
                    <button
                      key={item.id}
                      type="button"
                      className={`category-card ${item.slug === category ? "category-card-active" : ""}`}
                      onClick={() => setCategory(item.slug)}
                    >
                      <CategoryIcon category={{ name: item.name, slug: item.slug }} />
                      <span className="category-card-name">{item.name}</span>
                      <strong>{item.skill_count}</strong>
                    </button>
                  ))}
                </div>

                <div className="toolbar-row">
                  <Input.Search
                    placeholder="搜索技能名称、描述或分类"
                    size="large"
                    className="toolbar-search"
                    prefix={<SearchOutlined />}
                    value={searchInput}
                    onChange={(event) => setSearchInput(event.target.value)}
                    allowClear
                  />
                  <Select
                    size="large"
                    className="toolbar-sort"
                    value={sort}
                    onChange={setSort}
                    options={[
                      { label: "最新发布", value: "latest" },
                      { label: "下载量", value: "downloads" },
                      { label: "收藏量", value: "favorites" },
                      { label: "名称", value: "name" },
                    ]}
                  />
                </div>
              </div>
            )}
          </div>

          <div className="results-head">
            <div>
              <Typography.Text className="results-kicker">技能列表</Typography.Text>
              <Typography.Title level={3} className="results-title">
                {skillsQuery.data?.total ?? 0} 个技能正在广场中展示
              </Typography.Title>
            </div>
            <Space wrap className="results-actions">
              <Button className="portal-secondary-button" onClick={() => setCategory(undefined)}>
                查看全部技能
              </Button>
              <Button className="portal-primary-button" type="primary" onClick={onUploadEntry}>
                {canUpload ? "上传我的技能" : user ? "进入上传通道" : "登录后上传技能"}
              </Button>
            </Space>
          </div>

          {skillsQuery.isLoading ? (
            <Card className="skill-card skill-card-wide" variant="borderless">
              <div className="center-panel">
                <Spin size="large" />
              </div>
            </Card>
          ) : skillsQuery.isError ? (
            <Card className="skill-card skill-card-wide" variant="borderless">
              <Typography.Title level={4}>技能列表加载失败</Typography.Title>
              <Typography.Paragraph className="skill-summary">{(skillsQuery.error as Error).message}</Typography.Paragraph>
            </Card>
          ) : skillsQuery.data?.items.length ? (
            <>
              <section className="skills-grid">
                {skillsQuery.data.items.map((skill) => (
                  <SkillCard key={skill.id} skill={skill} onOpen={openSkillDetail} />
                ))}
              </section>
              <div className="pagination-row">
                <Pagination
                  current={page}
                  pageSize={pageSize}
                  total={skillsQuery.data.total}
                  showSizeChanger
                  onChange={(nextPage, nextPageSize) => {
                    setPage(nextPage);
                    setPageSize(nextPageSize);
                  }}
                />
              </div>
            </>
          ) : (
            <Card className="skill-card skill-card-wide" variant="borderless">
              <Typography.Text className="skill-avatar">S</Typography.Text>
              <Typography.Title level={4}>{hasFilters ? "没有匹配结果" : "当前没有已发布技能"}</Typography.Title>
              <Typography.Paragraph className="skill-summary">
                {hasFilters
                  ? "可以尝试更换分类、清空关键词，或切换排序方式继续查找。"
                  : totalPublishedSkills
                    ? "当前筛选条件下暂无可展示技能。"
                    : "当前数据库里还没有已发布技能，请通过前台或后台的真实上传、审核、发布流程生成数据。"}
              </Typography.Paragraph>
              <Empty description={hasFilters ? "当前筛选没有结果" : "暂无已发布技能"} />
            </Card>
          )}
        </div>
      </section>

      <section className="overview-section" id="overview-section">
        <div className="section-heading">
          <div>
            <Typography.Text className="section-kicker">平台概览</Typography.Text>
            <Typography.Title level={2} className="section-title">
              上传、审核、发布的主线放在后面补充说明
            </Typography.Title>
          </div>
          <Typography.Paragraph className="section-copy">
            首页先看技能，概览区只负责补充平台能力和流程，不再抢前面的浏览入口。
          </Typography.Paragraph>
        </div>

        <div className="overview-grid">
          <Card className="overview-card" variant="borderless">
            <div className="overview-card-kicker">交付主线</div>
            <Typography.Title level={3}>上传 → 审核 → 发布</Typography.Title>
            <div className="hero-flow-list">
              <div className="hero-flow-item">
                <span>01</span>
                <div>
                  <strong>上传技能包</strong>
                  <p>ZIP 校验、分类命中、版本号解析与入库</p>
                </div>
              </div>
              <div className="hero-flow-item">
                <span>02</span>
                <div>
                  <strong>人工审核</strong>
                  <p>审核记录、状态流转和版本治理统一沉淀</p>
                </div>
              </div>
              <div className="hero-flow-item">
                <span>03</span>
                <div>
                  <strong>正式发布</strong>
                  <p>前台即时可见，支持归档、回滚和下载统计</p>
                </div>
              </div>
            </div>
          </Card>

          <Card className="overview-card" variant="borderless">
            <div className="overview-card-kicker">体验说明</div>
            <Typography.Title level={3}>你能在前台直接完成两类动作</Typography.Title>
            <div className="overview-note-list">
              <div className="overview-note-item">
                <strong>探索与选择</strong>
                <p>分类筛选、详情页、收藏、下载都在技能广场里完成。</p>
              </div>
              <div className="overview-note-item">
                <strong>投稿与接力</strong>
                <p>具备权限的账号可以直接从前台提交 ZIP 技能包，后台继续完成审批与发布。</p>
              </div>
            </div>
            <div className="hero-category-cloud">
              {(categoriesQuery.data ?? []).slice(0, 6).map((item) => (
                <span key={item.id} className="hero-category-chip">
                  {item.name}
                </span>
              ))}
            </div>
          </Card>
        </div>
      </section>

      <Drawer
        title={detailQuery.data?.skill.name ?? "技能详情"}
        placement="right"
        width={720}
        open={Boolean(selectedSkillSlug)}
        onClose={closeSkillDetail}
        className="skill-detail-drawer"
        destroyOnHidden
      >
        {detailQuery.isLoading ? (
          <div className="center-panel">
            <Spin size="large" />
          </div>
        ) : detailQuery.isError ? (
          <Alert type="error" showIcon message={(detailQuery.error as Error).message} />
        ) : detailQuery.data ? (
          <SkillDetailContent
            detail={detailQuery.data}
            accessToken={accessToken}
            selectedUsageMode={selectedUsageMode}
            setUsageMode={setUsageMode}
            onOpenLogin={onOpenLogin}
          />
        ) : null}
      </Drawer>
    </>
  );
}

function SkillDetailRedirect() {
  const { slug } = useParams();
  return <Navigate to={slug ? `/categories?skill=${slug}&usage=agent` : "/categories"} replace />;
}

export default function App() {
  const queryClient = useQueryClient();
  const { accessToken, user, setSession, clearSession } = usePortalAuthStore();
  const [loginOpen, setLoginOpen] = useState(false);
  const [uploadOpen, setUploadOpen] = useState(false);
  const [uploadFiles, setUploadFiles] = useState<UploadFile[]>([]);
  const canUpload = hasPermission(user, "skill.upload");

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

  const uploadMutation = useMutation({
    mutationFn: async () => {
      const file = uploadFiles[0]?.originFileObj;
      if (!file) {
        throw new Error("请先选择一个 ZIP 技能包");
      }
      if (!accessToken) {
        throw new Error("请先登录后再上传");
      }
      const formData = new FormData();
      formData.append("file", file);
      return apiRequest<{ skill_id: string; version_id: string; created_skill: boolean; review_status: string }>("/admin/skills/upload", {
        method: "POST",
        token: accessToken,
        body: formData,
      });
    },
    onSuccess: async () => {
      setUploadFiles([]);
      await queryClient.invalidateQueries({ queryKey: ["public-skills"] });
    },
  });

  const handlePortalUploadEntry = () => {
    if (!user) {
      setLoginOpen(true);
      return;
    }
    if (canUpload) {
      uploadMutation.reset();
      setUploadFiles([]);
      setUploadOpen(true);
      return;
    }
    window.location.href = `${ADMIN_WEB_URL}/skills`;
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
      </Drawer>

      <Modal
        title="上传技能包"
        className="portal-upload-modal"
        open={uploadOpen}
        onCancel={() => {
          setUploadOpen(false);
          setUploadFiles([]);
          uploadMutation.reset();
        }}
        onOk={() => uploadMutation.mutate()}
        confirmLoading={uploadMutation.isPending}
        okText="开始上传"
        cancelText="暂不上传"
        okButtonProps={{ className: "portal-primary-button modal-submit-button" }}
        cancelButtonProps={{ className: "portal-secondary-button modal-cancel-button" }}
      >
        <div className="upload-modal-intro">
          <Typography.Paragraph>前台也可以直接提交技能包，审核通过并发布后会自动出现在当前广场。</Typography.Paragraph>
          <div className="upload-modal-hints">
            <span>仅支持 ZIP 技能包</span>
            <span>根目录必须包含 skill.yaml 与 README.md</span>
          </div>
        </div>
        <Upload.Dragger
          accept=".zip"
          maxCount={1}
          beforeUpload={() => false}
          fileList={uploadFiles}
          className="upload-dropzone"
          onChange={({ fileList: next }) => setUploadFiles(next)}
        >
          <p className="ant-upload-text">点击或拖拽上传技能 ZIP 包</p>
          <p className="ant-upload-hint">建议先在本地完成版本号与分类校验，再提交审核。</p>
        </Upload.Dragger>
        {uploadMutation.isSuccess ? (
          <Alert
            style={{ marginTop: 16 }}
            type="success"
            showIcon
            message="技能包已提交成功"
            description={
              <Space direction="vertical" size={4}>
                <span>当前版本状态：{uploadMutation.data.review_status}</span>
                <Button className="portal-link-button" type="link" href={`${ADMIN_WEB_URL}/skills/${uploadMutation.data.skill_id}`}>
                  去后台查看详情
                </Button>
              </Space>
            }
          />
        ) : null}
        {uploadMutation.error ? <Alert style={{ marginTop: 16 }} type="error" showIcon message={(uploadMutation.error as Error).message} /> : null}
      </Modal>
    </Layout>
  );
}
