/**
 * 组件约定：
 * - 承载技能详情抽屉的完整正文，包括摘要、README、usage guide、版本历史和互动区。
 * - 需要的 capability、统计和动作回调都由外层页面注入，组件内部不自行补状态机判断。
 */
import { LikeFilled, LikeOutlined } from "@ant-design/icons";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Alert, Button, Card, Space, Tag, Typography, message } from "antd";
import dayjs from "dayjs";

import { API_BASE_URL, apiRequest } from "../lib/api";
import type { PublicSkillDetailResponse } from "../lib/portalTypes";
import { CategoryIcon } from "./CategoryIcon";
import { UsageGuideSection } from "./UsageGuideSection";

export function SkillDetailContent({
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
      message.success(detail.is_favorited ? "已取消收藏" : "已加入收藏");
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["public-skills"] }),
        queryClient.invalidateQueries({ queryKey: ["public-skill-detail", detail.skill.slug] }),
      ]);
    },
    onError: (error: Error) => {
      message.error(error.message);
    },
  });

  const likeMutation = useMutation({
    mutationFn: async (liked: boolean) =>
      apiRequest(`/public/skills/${detail.skill.id}/like`, {
        method: liked ? "DELETE" : "POST",
        token: accessToken ?? undefined,
      }),
    onSuccess: async () => {
      message.success(detail.is_liked ? "已取消点赞" : "已点赞");
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["public-skills"] }),
        queryClient.invalidateQueries({ queryKey: ["public-skill-detail", detail.skill.slug] }),
      ]);
    },
    onError: (error: Error) => {
      message.error(error.message);
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
      const filename = disposition?.match(/filename="?([^"]+)"?/)?.[1] ?? `${detail.skill.slug}.zip`;
      anchor.href = downloadUrl;
      anchor.download = filename;
      anchor.click();
      URL.revokeObjectURL(downloadUrl);
    },
    onSuccess: async () => {
      message.success("下载已开始");
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["public-skills"] }),
        queryClient.invalidateQueries({ queryKey: ["public-skill-detail", detail.skill.slug] }),
      ]);
    },
    onError: (error: Error) => {
      message.error(error.message);
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
            id="portal-skill-detail-like-button"
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
            id="portal-skill-detail-favorite-button"
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
          <Button
            id="portal-skill-detail-download-button"
            className="portal-primary-button"
            type="primary"
            onClick={() => downloadMutation.mutate()}
            loading={downloadMutation.isPending}
          >
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

export function SkillDetailErrorState({ message }: { message: string }) {
  return <Alert type="error" showIcon message={message} />;
}
