import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Alert, Button, Card, Col, Descriptions, Form, Input, Progress, Row, Segmented, Select, Space, Table, Tag, Typography } from "antd";
import dayjs from "dayjs";
import { Link, useParams } from "react-router-dom";

import { SkillUploadModal } from "../components/SkillUploadModal";
import { apiRequest } from "../lib/api";
import { useAuthStore } from "../store/auth";

type SkillVersionSummary = {
  id: string;
  version: string;
  review_status: string;
  created_at: string;
  published_at: string | null;
};

type ReviewRecordItem = {
  id: string;
  action: string;
  comment: string;
  operator_display_name: string;
  created_at: string;
};

type SkillGrantItem = {
  id: string;
  target_type: "role" | "user";
  target_id: string;
  target_name: string;
  permission_scope: "owner" | "maintainer" | "reviewer" | "publisher" | "rollback" | "viewer";
  created_at: string;
};

type SkillStatsOverview = {
  skill_id: string;
  like_count: number;
  favorite_count: number;
  download_count: number;
  recent_downloads: Array<{ day: string; count: number }>;
  recent_favorites: Array<{ day: string; count: number }>;
  recent_likes: Array<{ day: string; count: number }>;
};

type SkillFavoriteRecord = {
  user_id: string;
  username: string;
  display_name: string;
  created_at: string;
};

type SkillDownloadRecord = {
  id: string;
  user_id: string | null;
  username: string | null;
  display_name: string | null;
  version: string;
  created_at: string;
  ip: string | null;
  user_agent: string | null;
};

type SkillDetailResponse = {
  skill: {
    id: string;
    name: string;
    slug: string;
    summary: string;
    description: string;
    status: string;
    category_name: string;
    category_slug: string;
    latest_version_no: string | null;
    current_published_version_id: string | null;
    owner_user_id: string;
    owner_display_name: string | null;
    download_count: number;
    favorite_count: number;
    like_count: number;
    published_at: string | null;
  };
  versions: SkillVersionSummary[];
  recent_reviews: ReviewRecordItem[];
  latest_version_status: string | null;
  current_published_version: string | null;
  pending_review_count: number;
  pending_release_count: number;
  capabilities: {
    edit_skill: boolean;
    upload_version: boolean;
    manage_grants: boolean;
    view_favorite_details: boolean;
    view_download_details: boolean;
    view_sensitive_download_details: boolean;
  };
};

type CategoryItem = {
  id: string;
  name: string;
  slug: string;
};

type RoleItem = {
  id: string;
  code: string;
  name: string;
  is_active: boolean;
};

type UserItem = {
  id: string;
  username: string;
  display_name: string;
  status: "active" | "disabled";
};

const SCOPE_OPTIONS = [
  { label: "Owner", value: "owner" },
  { label: "Maintainer", value: "maintainer" },
  { label: "Reviewer", value: "reviewer" },
  { label: "Publisher", value: "publisher" },
  { label: "Rollback", value: "rollback" },
  { label: "Viewer", value: "viewer" },
];

export function SkillDetailPage() {
  const { skillId } = useParams();
  const accessToken = useAuthStore((state) => state.accessToken);
  const queryClient = useQueryClient();
  const [uploadOpen, setUploadOpen] = useState(false);
  const [roleScope, setRoleScope] = useState<string>("reviewer");
  const [selectedRoleIds, setSelectedRoleIds] = useState<string[]>([]);
  const [userScope, setUserScope] = useState<string>("maintainer");
  const [selectedUserIds, setSelectedUserIds] = useState<string[]>([]);
  const [statsWindow, setStatsWindow] = useState<"7" | "30">("7");

  const detailQuery = useQuery({
    queryKey: ["admin-skill-detail", accessToken, skillId],
    enabled: Boolean(skillId && accessToken),
    queryFn: () => apiRequest<SkillDetailResponse>(`/admin/skills/${skillId}`, { token: accessToken }),
  });

  const categoriesQuery = useQuery({
    queryKey: ["admin-skill-detail-categories", accessToken],
    queryFn: () => apiRequest<CategoryItem[]>("/admin/categories/options", { token: accessToken }),
  });

  const rolesQuery = useQuery({
    queryKey: ["admin-skill-role-options", accessToken],
    enabled: Boolean(accessToken && detailQuery.data?.capabilities.manage_grants),
    queryFn: () => apiRequest<RoleItem[]>("/admin/roles/options", { token: accessToken }),
  });

  const usersQuery = useQuery({
    queryKey: ["admin-skill-user-options", accessToken],
    enabled: Boolean(accessToken && detailQuery.data?.capabilities.manage_grants),
    queryFn: () => apiRequest<UserItem[]>("/admin/users/options?status=active", { token: accessToken }),
  });

  const grantsQuery = useQuery({
    queryKey: ["admin-skill-grants", accessToken, skillId],
    enabled: Boolean(skillId && accessToken),
    queryFn: () => apiRequest<SkillGrantItem[]>(`/admin/skills/${skillId}/permissions`, { token: accessToken }),
  });

  const statsQuery = useQuery({
    queryKey: ["admin-skill-stats", accessToken, skillId],
    enabled: Boolean(skillId && accessToken),
    queryFn: () => apiRequest<SkillStatsOverview>(`/admin/skills/${skillId}/stats`, { token: accessToken }),
  });

  const favoritesQuery = useQuery({
    queryKey: ["admin-skill-favorites", accessToken, skillId],
    enabled: Boolean(skillId && accessToken && detailQuery.data?.capabilities.view_favorite_details),
    queryFn: () => apiRequest<SkillFavoriteRecord[]>(`/admin/skills/${skillId}/favorites`, { token: accessToken }),
  });

  const downloadsQuery = useQuery({
    queryKey: ["admin-skill-downloads", accessToken, skillId],
    enabled: Boolean(skillId && accessToken && detailQuery.data?.capabilities.view_download_details),
    queryFn: () => apiRequest<SkillDownloadRecord[]>(`/admin/skills/${skillId}/downloads`, { token: accessToken }),
  });

  const updateMutation = useMutation({
    mutationFn: (values: { name: string; summary: string; description: string; category_slug: string }) =>
      apiRequest(`/admin/skills/${skillId}`, {
        method: "PATCH",
        token: accessToken,
        body: JSON.stringify(values),
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["admin-skill-detail", accessToken, skillId] });
      await queryClient.invalidateQueries({ queryKey: ["admin-skill-list"] });
    },
  });

  const roleGrantMutation = useMutation({
    mutationFn: () =>
      apiRequest<SkillGrantItem[]>(`/admin/skills/${skillId}/role-grants`, {
        method: "POST",
        token: accessToken,
        body: JSON.stringify({ target_ids: selectedRoleIds, permission_scope: roleScope }),
      }),
    onSuccess: async () => {
      setSelectedRoleIds([]);
      await queryClient.invalidateQueries({ queryKey: ["admin-skill-grants", accessToken, skillId] });
    },
  });

  const userGrantMutation = useMutation({
    mutationFn: () =>
      apiRequest<SkillGrantItem[]>(`/admin/skills/${skillId}/user-grants`, {
        method: "POST",
        token: accessToken,
        body: JSON.stringify({ target_ids: selectedUserIds, permission_scope: userScope }),
      }),
    onSuccess: async () => {
      setSelectedUserIds([]);
      await queryClient.invalidateQueries({ queryKey: ["admin-skill-grants", accessToken, skillId] });
    },
  });

  const deleteGrantMutation = useMutation({
    mutationFn: ({ grantId, targetType }: { grantId: string; targetType: "role" | "user" }) =>
      apiRequest(`/admin/skills/${skillId}/${targetType}-grants/${grantId}`, {
        method: "DELETE",
        token: accessToken,
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["admin-skill-grants", accessToken, skillId] });
    },
  });

  const initialValues = useMemo(
    () =>
      detailQuery.data
        ? {
            name: detailQuery.data.skill.name,
            summary: detailQuery.data.skill.summary,
            description: detailQuery.data.skill.description,
            category_slug: detailQuery.data.skill.category_slug,
          }
        : undefined,
    [detailQuery.data],
  );

  const capabilities = detailQuery.data?.capabilities;
  const canManageSkill = capabilities?.edit_skill ?? false;
  const canUploadVersion = capabilities?.upload_version ?? false;
  const canManageGrants = capabilities?.manage_grants ?? false;
  const canViewFavoriteDetails = capabilities?.view_favorite_details ?? false;
  const canViewDownloadDetails = capabilities?.view_download_details ?? false;
  const canViewSensitiveDownloadDetails = capabilities?.view_sensitive_download_details ?? false;
  const statsDays = Number(statsWindow);

  const statsCards = detailQuery.data && statsQuery.data
    ? [
        { label: "点赞", value: statsQuery.data.like_count, color: "#c2185b" },
        { label: "收藏", value: statsQuery.data.favorite_count, color: "#b26a00" },
        { label: "下载", value: statsQuery.data.download_count, color: "#237804" },
      ]
    : [];

  const trendRows = statsQuery.data
    ? [
        { key: "likes", label: "点赞", points: statsQuery.data.recent_likes.slice(0, statsDays) },
        { key: "favorites", label: "收藏", points: statsQuery.data.recent_favorites.slice(0, statsDays) },
        { key: "downloads", label: "下载", points: statsQuery.data.recent_downloads.slice(0, statsDays) },
      ]
    : [];

  return (
    <>
      {detailQuery.isError ? <Alert type="error" showIcon message={(detailQuery.error as Error).message} /> : null}

      {detailQuery.data ? (
        <>
          <Row gutter={[16, 16]}>
            <Col xs={24} xl={14}>
              <Card id="admin-skill-detail-main-info-card" className="content-card detail-card" title="主档信息">
                <Descriptions column={2}>
                  <Descriptions.Item label="名称">{detailQuery.data.skill.name}</Descriptions.Item>
                  <Descriptions.Item label="Slug">{detailQuery.data.skill.slug}</Descriptions.Item>
                  <Descriptions.Item label="分类">{detailQuery.data.skill.category_name}</Descriptions.Item>
                  <Descriptions.Item label="状态">
                    <Tag color={detailQuery.data.skill.status === "active" ? "green" : "default"}>
                      {detailQuery.data.skill.status}
                    </Tag>
                  </Descriptions.Item>
                  <Descriptions.Item label="负责人">{detailQuery.data.skill.owner_display_name ?? "-"}</Descriptions.Item>
                  <Descriptions.Item label="当前线上版本">
                    {detailQuery.data.current_published_version ? `v${detailQuery.data.current_published_version}` : "未发布"}
                  </Descriptions.Item>
                  <Descriptions.Item label="最新版本状态">
                    <Tag>{detailQuery.data.latest_version_status ?? "unknown"}</Tag>
                  </Descriptions.Item>
                  <Descriptions.Item label="发布时间">
                    {detailQuery.data.skill.published_at ? dayjs(detailQuery.data.skill.published_at).format("YYYY-MM-DD HH:mm") : "-"}
                  </Descriptions.Item>
                  <Descriptions.Item label="待审核">{detailQuery.data.pending_review_count}</Descriptions.Item>
                  <Descriptions.Item label="待发布">{detailQuery.data.pending_release_count}</Descriptions.Item>
                  <Descriptions.Item label="下载量">{detailQuery.data.skill.download_count}</Descriptions.Item>
                  <Descriptions.Item label="收藏量">{detailQuery.data.skill.favorite_count}</Descriptions.Item>
                  <Descriptions.Item label="点赞量">{detailQuery.data.skill.like_count}</Descriptions.Item>
                </Descriptions>
                <Space style={{ marginTop: 16 }}>
                  {canUploadVersion ? (
                    <Button type="primary" onClick={() => setUploadOpen(true)}>
                      上传新版本
                    </Button>
                  ) : (
                    <Typography.Text type="secondary">当前账号对该技能没有上传新版本权限。</Typography.Text>
                  )}
                </Space>
              </Card>
            </Col>
            <Col xs={24} xl={10}>
              <Card id="admin-skill-detail-editor-card" className="content-card detail-card" title="编辑展示信息">
                <div id="admin-skill-detail-editor-form">
                  <Form
                    layout="vertical"
                    initialValues={initialValues}
                    onFinish={(values) => updateMutation.mutate(values)}
                    disabled={!canManageSkill}
                  >
                    <Form.Item label="名称" name="name" rules={[{ required: true }]}>
                      <Input />
                    </Form.Item>
                    <Form.Item label="摘要" name="summary" rules={[{ required: true }]}>
                      <Input.TextArea rows={3} />
                    </Form.Item>
                    <Form.Item label="详细描述" name="description" rules={[{ required: true }]}>
                      <Input.TextArea rows={5} />
                    </Form.Item>
                    <Form.Item label="分类" name="category_slug" rules={[{ required: true }]}>
                      <Select
                        options={(categoriesQuery.data ?? []).map((item) => ({
                          label: item.name,
                          value: item.slug,
                        }))}
                      />
                    </Form.Item>
                    {updateMutation.error ? (
                      <Alert type="error" showIcon message={(updateMutation.error as Error).message} />
                    ) : null}
                    {!canManageSkill ? (
                      <Typography.Text type="secondary">当前账号对该技能只有只读权限，不能修改主档信息。</Typography.Text>
                    ) : null}
                    <Button type="primary" htmlType="submit" loading={updateMutation.isPending} disabled={!canManageSkill}>
                      保存主档
                    </Button>
                  </Form>
                </div>
              </Card>
            </Col>
          </Row>

          <Card id="admin-skill-detail-versions-card" className="content-card" title="版本时间线">
            <div id="admin-skill-detail-versions-table-container">
              <Table
                rowKey="id"
                pagination={false}
                dataSource={detailQuery.data.versions}
                columns={[
                  {
                    title: "版本",
                    dataIndex: "version",
                    render: (_: string, record: SkillVersionSummary) => <Link to={`/versions/${record.id}`}>{record.version}</Link>,
                  },
                  {
                    title: "状态",
                    dataIndex: "review_status",
                    render: (value: string) => <Tag>{value}</Tag>,
                  },
                  {
                    title: "创建时间",
                    dataIndex: "created_at",
                    render: (value: string) => dayjs(value).format("YYYY-MM-DD HH:mm"),
                  },
                  {
                    title: "发布时间",
                    dataIndex: "published_at",
                    render: (value: string | null) => (value ? dayjs(value).format("YYYY-MM-DD HH:mm") : "-"),
                  },
                ]}
              />
            </div>
          </Card>

          <Card id="admin-skill-detail-recent-audit-card" className="content-card" title="最近审核记录">
            <div id="admin-skill-detail-recent-audit-table-container">
              <Table
                rowKey="id"
                pagination={false}
                dataSource={detailQuery.data.recent_reviews}
                columns={[
                  { title: "动作", dataIndex: "action" },
                  { title: "操作人", dataIndex: "operator_display_name" },
                  { title: "说明", dataIndex: "comment", render: (value: string) => value || "-" },
                  {
                    title: "时间",
                    dataIndex: "created_at",
                    render: (value: string) => dayjs(value).format("YYYY-MM-DD HH:mm"),
                  },
                ]}
              />
            </div>
          </Card>

          <Row gutter={[16, 16]}>
            <Col xs={24} xl={12}>
              <Card id="admin-skill-detail-grants-card" className="content-card detail-card" title="授权对象">
                <Space direction="vertical" size={16} style={{ width: "100%" }}>
                  <Space wrap>
                    <Select value={roleScope} onChange={setRoleScope} options={SCOPE_OPTIONS} style={{ width: 160 }} />
                    <Select
                      mode="multiple"
                      placeholder="给角色授权"
                      value={selectedRoleIds}
                      onChange={setSelectedRoleIds}
                      style={{ minWidth: 280 }}
                      options={(rolesQuery.data ?? [])
                        .filter((item) => item.is_active)
                        .map((item) => ({ label: `${item.name} (${item.code})`, value: item.id }))}
                      disabled={!canManageGrants}
                    />
                    <Button type="primary" onClick={() => roleGrantMutation.mutate()} disabled={!canManageGrants || !selectedRoleIds.length}>
                      授予角色
                    </Button>
                  </Space>
                  <Space wrap>
                    <Select value={userScope} onChange={setUserScope} options={SCOPE_OPTIONS} style={{ width: 160 }} />
                    <Select
                      mode="multiple"
                      placeholder="给指定用户授权"
                      value={selectedUserIds}
                      onChange={setSelectedUserIds}
                      style={{ minWidth: 280 }}
                      options={(usersQuery.data ?? [])
                        .filter((item) => item.status === "active")
                        .map((item) => ({ label: `${item.display_name} (${item.username})`, value: item.id }))}
                      disabled={!canManageGrants}
                    />
                    <Button type="primary" onClick={() => userGrantMutation.mutate()} disabled={!canManageGrants || !selectedUserIds.length}>
                      授予用户
                    </Button>
                  </Space>
                  {!canManageGrants ? (
                    <Typography.Text type="secondary">只有该技能的 owner 才能配置授权对象。</Typography.Text>
                  ) : null}
                  {roleGrantMutation.error ? <Alert type="error" showIcon message={(roleGrantMutation.error as Error).message} /> : null}
                  {userGrantMutation.error ? <Alert type="error" showIcon message={(userGrantMutation.error as Error).message} /> : null}
                  <div id="admin-skill-detail-grants-table-container">
                    <Table
                      rowKey="id"
                      pagination={false}
                      dataSource={grantsQuery.data ?? []}
                      columns={[
                        { title: "类型", dataIndex: "target_type", render: (value: string) => <Tag>{value === "role" ? "角色" : "用户"}</Tag> },
                        { title: "对象", dataIndex: "target_name" },
                        { title: "授权范围", dataIndex: "permission_scope", render: (value: string) => <Tag color="blue">{value}</Tag> },
                        {
                          title: "授权时间",
                          dataIndex: "created_at",
                          render: (value: string) => dayjs(value).format("YYYY-MM-DD HH:mm"),
                        },
                        {
                          title: "操作",
                          render: (_: unknown, record: SkillGrantItem) => (
                            <Button
                              size="small"
                              danger
                              disabled={!canManageGrants}
                              loading={deleteGrantMutation.isPending}
                              onClick={() => deleteGrantMutation.mutate({ grantId: record.id, targetType: record.target_type })}
                            >
                              移除
                            </Button>
                          ),
                        },
                      ]}
                    />
                  </div>
                </Space>
              </Card>
            </Col>
            <Col xs={24} xl={12}>
              <Card id="admin-skill-detail-stats-card" className="content-card detail-card" title="数据统计">
                {statsQuery.data ? (
                  <Space direction="vertical" size={12} style={{ width: "100%" }}>
                    <Space wrap>
                      {statsCards.map((item) => (
                        <Card key={item.label} size="small" style={{ minWidth: 110 }}>
                          <Typography.Text type="secondary">{item.label}</Typography.Text>
                          <Typography.Title level={4} style={{ margin: "8px 0 0", color: item.color }}>
                            {item.value}
                          </Typography.Title>
                        </Card>
                      ))}
                    </Space>
                    <Space align="center" wrap>
                      <Typography.Text strong>趋势窗口</Typography.Text>
                      <Segmented
                        value={statsWindow}
                        onChange={(value) => setStatsWindow(value as "7" | "30")}
                        options={[
                          { label: "最近 7 天", value: "7" },
                          { label: "最近 30 天", value: "30" },
                        ]}
                      />
                    </Space>
                    <div id="admin-skill-detail-trend-table-container">
                      <Table
                        rowKey="key"
                        pagination={false}
                        size="small"
                        dataSource={trendRows}
                        columns={[
                          { title: "指标", dataIndex: "label", width: 80 },
                          {
                            title: `${statsWindow} 天趋势`,
                            render: (_: unknown, record: { points: Array<{ day: string; count: number }> }) =>
                              record.points.length ? (
                                <Space direction="vertical" size={8} style={{ width: "100%" }}>
                                  {record.points.map((point) => (
                                    <div key={`${record.points.length}-${point.day}`}>
                                      <div style={{ display: "flex", justifyContent: "space-between", gap: 12 }}>
                                        <Typography.Text>{point.day}</Typography.Text>
                                        <Typography.Text>{point.count}</Typography.Text>
                                      </div>
                                      <Progress percent={Math.max(point.count, 0)} showInfo={false} strokeColor="#1677ff" />
                                    </div>
                                  ))}
                                </Space>
                              ) : (
                                <Typography.Text type="secondary">暂无数据</Typography.Text>
                              ),
                          },
                        ]}
                      />
                    </div>
                  </Space>
                ) : null}
              </Card>
            </Col>
          </Row>

          <Row gutter={[16, 16]}>
            <Col xs={24} xl={12}>
              <Card id="admin-skill-detail-favorites-card" className="content-card" title="收藏明细">
                {canViewFavoriteDetails ? (
                  <div id="admin-skill-detail-favorites-table-container">
                    <Table
                      rowKey={(record) => `${record.user_id}-${record.created_at}`}
                      pagination={{ pageSize: 8 }}
                      dataSource={favoritesQuery.data ?? []}
                      columns={[
                        { title: "用户", render: (_: unknown, record: SkillFavoriteRecord) => `${record.display_name} (${record.username})` },
                        {
                          title: "收藏时间",
                          dataIndex: "created_at",
                          render: (value: string) => dayjs(value).format("YYYY-MM-DD HH:mm"),
                        },
                      ]}
                    />
                  </div>
                ) : (
                  <Typography.Text type="secondary">当前账号没有查看收藏明细的权限。</Typography.Text>
                )}
              </Card>
            </Col>
            <Col xs={24} xl={12}>
              <Card id="admin-skill-detail-downloads-card" className="content-card" title="下载明细">
                {canViewDownloadDetails ? (
                  <div id="admin-skill-detail-downloads-table-container">
                    <Table
                      rowKey="id"
                      pagination={{ pageSize: 8 }}
                      dataSource={downloadsQuery.data ?? []}
                      columns={[
                        {
                          title: "用户",
                          render: (_: unknown, record: SkillDownloadRecord) =>
                            record.display_name ? `${record.display_name} (${record.username ?? "-"})` : "匿名下载（已脱敏）",
                        },
                        { title: "版本", dataIndex: "version" },
                        ...(canViewSensitiveDownloadDetails
                          ? [{ title: "IP", dataIndex: "ip", render: (value: string | null) => value ?? "-" }]
                          : []),
                        {
                          title: "下载时间",
                          dataIndex: "created_at",
                          render: (value: string) => dayjs(value).format("YYYY-MM-DD HH:mm"),
                        },
                      ]}
                    />
                  </div>
                ) : (
                  <Typography.Text type="secondary">当前账号没有查看下载明细的权限。</Typography.Text>
                )}
              </Card>
            </Col>
          </Row>
        </>
      ) : null}

      {canUploadVersion ? (
        <SkillUploadModal
          open={uploadOpen}
          modalId="admin-skill-detail-upload-modal"
          token={accessToken}
          onClose={() => setUploadOpen(false)}
          onSuccess={async () => {
            await queryClient.invalidateQueries({ queryKey: ["admin-skill-detail", accessToken, skillId] });
            await queryClient.invalidateQueries({ queryKey: ["admin-skill-list"] });
          }}
        />
      ) : null}
    </>
  );
}
