import { useQuery } from "@tanstack/react-query";
import { Button, Card, Col, Empty, Row, Space, Statistic, Table, Tag, Typography } from "antd";
import dayjs from "dayjs";
import { Link } from "react-router-dom";

import { apiRequest } from "../lib/api";
import { hasPermission } from "../lib/permissions";
import { useAuthStore } from "../store/auth";

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

type AdminSkillListItem = {
  id: string;
  name: string;
  slug: string;
  status: string;
  category_name: string;
  category_slug: string;
  latest_version_no: string | null;
  current_published_version_id: string | null;
  latest_version_status: string | null;
  current_published_version: string | null;
  pending_review_count: number;
  pending_release_count: number;
  published_at: string | null;
  created_at: string;
  updated_at: string;
};

type ReviewQueueItem = {
  version_id: string;
  skill_id: string;
  skill_name: string;
  skill_slug: string;
  version: string;
  category_name: string;
  created_by_display_name: string;
  created_at: string;
  review_status: string;
  latest_review_comment: string | null;
  latest_action_at: string | null;
};

type PendingReleaseItem = {
  version_id: string;
  skill_id: string;
  skill_name: string;
  skill_slug: string;
  version: string;
  category_name: string;
  created_by_display_name: string;
  approved_at: string | null;
  latest_review_comment: string | null;
};

type ReviewHistoryItem = {
  version_id: string;
  skill_id: string;
  skill_name: string;
  version: string;
  category_name: string;
  action: string;
  comment: string;
  operator_display_name: string;
  created_at: string;
};

type PagedResponse<T> = {
  items: T[];
  total: number;
  page: number;
  page_size: number;
};

const recentSkillColumns = [
  {
    title: "技能",
    render: (_: unknown, record: AdminSkillListItem) => <Link to={`/skills/${record.id}`}>{record.name}</Link>,
  },
  { title: "分类", dataIndex: "category_name" },
  {
    title: "版本状态",
    dataIndex: "latest_version_status",
    render: (value: string | null) => <Tag color={value === "published" ? "green" : "default"}>{value ?? "unknown"}</Tag>,
  },
  {
    title: "待办",
    render: (_: unknown, record: AdminSkillListItem) => (
      <Space wrap>
        <Tag color="gold">待审核 {record.pending_review_count}</Tag>
        <Tag color="cyan">待发布 {record.pending_release_count}</Tag>
      </Space>
    ),
  },
];

export function DashboardPage() {
  const accessToken = useAuthStore((state) => state.accessToken);
  const user = useAuthStore((state) => state.user);
  const canViewSkills = hasPermission(user, "skill.view");
  const canViewCategories = hasPermission(user, "admin.categories.view");
  const canReview = hasPermission(user, "skill.review");
  const canPublish = hasPermission(user, "skill.publish");
  const canViewHistory = hasPermission(user, "skill.view");

  const categoriesQuery = useQuery({
    queryKey: ["admin-dashboard-categories", accessToken],
    enabled: Boolean(accessToken && canViewCategories),
    queryFn: () => apiRequest<CategoryItem[]>("/admin/categories", { token: accessToken }),
  });

  const skillsQuery = useQuery({
    queryKey: ["admin-dashboard-skills", accessToken],
    enabled: Boolean(accessToken && canViewSkills),
    queryFn: () => apiRequest<PagedResponse<AdminSkillListItem>>("/admin/skills?page=1&page_size=6", { token: accessToken }),
  });

  const publicSkillsQuery = useQuery({
    queryKey: ["admin-dashboard-public-skills-count"],
    enabled: canViewSkills,
    queryFn: () => apiRequest<PagedResponse<{ id: string }>>("/public/skills?page=1&page_size=1"),
  });

  const pendingReviewsQuery = useQuery({
    queryKey: ["admin-dashboard-pending-reviews", accessToken],
    enabled: Boolean(accessToken && canReview),
    queryFn: () => apiRequest<ReviewQueueItem[]>("/admin/reviews/pending", { token: accessToken }),
  });

  const pendingReleasesQuery = useQuery({
    queryKey: ["admin-dashboard-pending-releases", accessToken],
    enabled: Boolean(accessToken && canPublish),
    queryFn: () => apiRequest<PendingReleaseItem[]>("/admin/releases/pending", { token: accessToken }),
  });

  const historyQuery = useQuery({
    queryKey: ["admin-dashboard-review-history", accessToken],
    enabled: Boolean(accessToken && canViewHistory),
    queryFn: () => apiRequest<ReviewHistoryItem[]>("/admin/reviews/history", { token: accessToken }),
  });

  return (
    <>
      <Row gutter={[16, 16]}>
        <Col xs={24} md={12} xl={6}>
          <Card id="admin-dashboard-stat-skill-total">
            <Statistic title="技能主档数" value={skillsQuery.data?.total ?? 0} loading={skillsQuery.isLoading} />
          </Card>
        </Col>
        <Col xs={24} md={12} xl={6}>
          <Card id="admin-dashboard-stat-public-skills">
            <Statistic title="已发布技能" value={publicSkillsQuery.data?.total ?? 0} loading={publicSkillsQuery.isLoading} />
          </Card>
        </Col>
        <Col xs={24} md={12} xl={6}>
          <Card id="admin-dashboard-stat-pending-reviews">
            <Statistic title="待审核版本" value={pendingReviewsQuery.data?.length ?? 0} loading={pendingReviewsQuery.isLoading} />
          </Card>
        </Col>
        <Col xs={24} md={12} xl={6}>
          <Card id="admin-dashboard-stat-pending-releases">
            <Statistic title="待发布版本" value={pendingReleasesQuery.data?.length ?? 0} loading={pendingReleasesQuery.isLoading} />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        <Col xs={24} xl={12}>
          <Card className="content-card" id="admin-dashboard-pending-reviews-card" title="待审核概览">
            {canReview ? (
              pendingReviewsQuery.data?.length ? (
                <div id="admin-dashboard-pending-reviews-table-container">
                  <Table
                    rowKey="version_id"
                    pagination={false}
                    dataSource={pendingReviewsQuery.data.slice(0, 6)}
                    columns={[
                      {
                        title: "技能",
                        render: (_: unknown, record: ReviewQueueItem) => (
                          <Link to={`/versions/${record.version_id}`}>{record.skill_name}</Link>
                        ),
                      },
                      { title: "版本", dataIndex: "version" },
                      { title: "提交人", dataIndex: "created_by_display_name" },
                      {
                        title: "提交时间",
                        dataIndex: "created_at",
                        render: (value: string) => dayjs(value).format("YYYY-MM-DD HH:mm"),
                      },
                    ]}
                  />
                </div>
              ) : (
                <Empty description="当前没有待审核版本" />
              )
            ) : (
              <Typography.Text type="secondary">当前账号没有审核中心访问权限。</Typography.Text>
            )}
          </Card>
        </Col>
        <Col xs={24} xl={12}>
          <Card className="content-card" id="admin-dashboard-pending-releases-card" title="待发布概览">
            {canPublish ? (
              pendingReleasesQuery.data?.length ? (
                <div id="admin-dashboard-pending-releases-table-container">
                  <Table
                    rowKey="version_id"
                    pagination={false}
                    dataSource={pendingReleasesQuery.data.slice(0, 6)}
                    columns={[
                      {
                        title: "技能",
                        render: (_: unknown, record: PendingReleaseItem) => (
                          <Link to={`/versions/${record.version_id}`}>{record.skill_name}</Link>
                        ),
                      },
                      { title: "版本", dataIndex: "version" },
                      {
                        title: "通过时间",
                        dataIndex: "approved_at",
                        render: (value: string | null) => (value ? dayjs(value).format("YYYY-MM-DD HH:mm") : "-"),
                      },
                      {
                        title: "最近意见",
                        dataIndex: "latest_review_comment",
                        render: (value: string | null) => value ?? "-",
                      },
                    ]}
                  />
                </div>
              ) : (
                <Empty description="当前没有待发布版本" />
              )
            ) : (
              <Typography.Text type="secondary">当前账号没有发布队列访问权限。</Typography.Text>
            )}
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        <Col xs={24} xl={14} className="dashboard-equal-height-col">
          <Card className="content-card dashboard-equal-height-card" id="admin-dashboard-recent-updates-card" title="最近更新技能">
            {skillsQuery.isError ? (
              <Typography.Text type="danger">{(skillsQuery.error as Error).message}</Typography.Text>
            ) : skillsQuery.data?.items.length ? (
              <div id="admin-dashboard-recent-updates-table-container">
                <Table rowKey="id" pagination={false} columns={recentSkillColumns} dataSource={skillsQuery.data.items} />
              </div>
            ) : (
              <Empty description="当前还没有技能主档数据" />
            )}
          </Card>
        </Col>
        <Col xs={24} xl={10} className="dashboard-equal-height-col">
          <Card className="content-card dashboard-equal-height-card" id="admin-dashboard-recent-history-card" title="最近处理记录">
            {canViewHistory ? (
              historyQuery.data?.length ? (
                <div id="admin-dashboard-recent-history-table-container">
                  <Table
                    rowKey={(record) => `${record.version_id}-${record.created_at}`}
                    pagination={false}
                    dataSource={historyQuery.data.slice(0, 8)}
                    columns={[
                      { title: "动作", dataIndex: "action", render: (value: string) => <Tag>{value}</Tag> },
                      { title: "技能", dataIndex: "skill_name" },
                      { title: "操作人", dataIndex: "operator_display_name" },
                      {
                        title: "时间",
                        dataIndex: "created_at",
                        render: (value: string) => dayjs(value).format("YYYY-MM-DD HH:mm"),
                      },
                    ]}
                  />
                </div>
              ) : (
                <Empty description="最近没有处理记录" />
              )
            ) : (
              <Typography.Text type="secondary">当前账号没有查看处理记录的权限。</Typography.Text>
            )}
          </Card>
        </Col>
      </Row>

      <Card className="content-card" id="admin-dashboard-categories-overview-card" title="分类概览">
        {canViewCategories ? (
          categoriesQuery.isError ? (
            <Typography.Text type="danger">{(categoriesQuery.error as Error).message}</Typography.Text>
          ) : categoriesQuery.data?.length ? (
            <div id="admin-dashboard-categories-overview-table-container">
              <Table
                rowKey="id"
                pagination={false}
                dataSource={categoriesQuery.data}
                columns={[
                  { title: "分类", dataIndex: "name" },
                  { title: "Slug", dataIndex: "slug" },
                  { title: "技能数", dataIndex: "skill_count" },
                  {
                    title: "展示",
                    dataIndex: "is_visible",
                    render: (value: boolean) => <Tag color={value ? "green" : "default"}>{value ? "显示" : "隐藏"}</Tag>,
                  },
                ]}
              />
            </div>
          ) : (
            <Empty description="暂无分类数据" />
          )
        ) : (
          <Typography.Text type="secondary">当前账号没有分类治理权限，首页不展示分类概览。</Typography.Text>
        )}
      </Card>
    </>
  );
}
