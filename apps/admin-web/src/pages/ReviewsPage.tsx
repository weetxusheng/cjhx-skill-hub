import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Alert, Button, Card, Input, Select, Space, Table, Tag, Typography } from "antd";
import dayjs from "dayjs";
import { Link } from "react-router-dom";

import { VersionActionModal } from "../components/VersionActionModal";
import { apiRequest } from "../lib/api";
import { hasPermission } from "../lib/permissions";
import { useAuthStore } from "../store/auth";

type ReviewItem = {
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
  assigned_reviewers: string[];
  assigned_publishers: string[];
};

type CategoryItem = {
  id: string;
  name: string;
  slug: string;
};

export function ReviewsPage() {
  const accessToken = useAuthStore((state) => state.accessToken);
  const user = useAuthStore((state) => state.user);
  const queryClient = useQueryClient();
  const [actionState, setActionState] = useState<{ versionId: string; action: "approve" | "reject" } | null>(null);
  const [categoryFilter, setCategoryFilter] = useState<string | undefined>();
  const [creatorFilter, setCreatorFilter] = useState("");
  const canReview = hasPermission(user, "skill.review");

  const categoriesQuery = useQuery({
    queryKey: ["admin-review-categories", accessToken],
    queryFn: () => apiRequest<CategoryItem[]>("/admin/categories/options", { token: accessToken }),
  });

  const reviewsQuery = useQuery({
    queryKey: ["admin-review-queue", accessToken, categoryFilter, creatorFilter],
    queryFn: () => {
      const query = new URLSearchParams();
      if (categoryFilter) {
        query.set("category", categoryFilter);
      }
      if (creatorFilter.trim()) {
        query.set("created_by", creatorFilter.trim());
      }
      return apiRequest<ReviewItem[]>(`/admin/reviews${query.size ? `?${query.toString()}` : ""}`, { token: accessToken });
    },
  });

  const actionMutation = useMutation({
    mutationFn: ({ versionId, action, comment }: { versionId: string; action: "approve" | "reject"; comment: string }) =>
      apiRequest(`/admin/versions/${versionId}/${action}`, {
        method: "POST",
        token: accessToken,
        body: JSON.stringify({ comment }),
      }),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["admin-review-queue"] }),
        queryClient.invalidateQueries({ queryKey: ["admin-version-detail"] }),
      ]);
      setActionState(null);
    },
  });

  return (
    <>
      <Card id="admin-reviews-filters-card" className="content-card filters-card">
        <Space wrap className="filters-row">
          <Select
            allowClear
            placeholder="按分类筛选"
            value={categoryFilter}
            onChange={setCategoryFilter}
            className="filters-select"
            options={(categoriesQuery.data ?? []).map((item) => ({ label: item.name, value: item.name }))}
          />
          <Input.Search
            allowClear
            value={creatorFilter}
            onChange={(event) => setCreatorFilter(event.target.value)}
            placeholder="搜索提交人"
            className="filters-search"
          />
          <Tag color="processing">待审版本 {reviewsQuery.data?.length ?? 0}</Tag>
          {!canReview ? <Tag>当前账号仅可查看，不能执行审核</Tag> : null}
        </Space>
      </Card>
      <Card id="admin-reviews-table-card" className="content-card">
        {reviewsQuery.isError ? (
          <Alert type="error" showIcon message={(reviewsQuery.error as Error).message} />
        ) : (
          <div id="admin-reviews-table-container">
            <Table
              rowKey="version_id"
              pagination={false}
              dataSource={reviewsQuery.data ?? []}
              columns={[
                {
                  title: "技能",
                  dataIndex: "skill_name",
                  render: (_: string, record: ReviewItem) => <Link to={`/versions/${record.version_id}`}>{record.skill_name}</Link>,
                },
                { title: "版本", dataIndex: "version" },
                { title: "分类", dataIndex: "category_name" },
                { title: "提交人", dataIndex: "created_by_display_name" },
                {
                  title: "审核负责人",
                  dataIndex: "assigned_reviewers",
                  render: (value: string[] | null | undefined) => {
                    const items = value ?? [];
                    return items.length
                      ? items.map((item) => <Tag key={item}>{item}</Tag>)
                      : <Typography.Text type="secondary">未配置</Typography.Text>;
                  },
                },
                {
                  title: "最近说明",
                  dataIndex: "latest_review_comment",
                  render: (value: string | null) => value || "-",
                },
                {
                  title: "状态",
                  dataIndex: "review_status",
                  render: (value: string) => <Tag>{value}</Tag>,
                },
                {
                  title: "提交时间",
                  dataIndex: "created_at",
                  render: (value: string) => dayjs(value).format("YYYY-MM-DD HH:mm"),
                },
                {
                  title: "最近动作时间",
                  dataIndex: "latest_action_at",
                  render: (value: string | null) => (value ? dayjs(value).format("YYYY-MM-DD HH:mm") : "-"),
                },
                {
                  title: "操作",
                  render: (_: unknown, record: ReviewItem) => (
                    canReview ? (
                      <Space size={8}>
                        <Button size="small" onClick={() => setActionState({ versionId: record.version_id, action: "approve" })}>
                          通过
                        </Button>
                        <Button size="small" danger onClick={() => setActionState({ versionId: record.version_id, action: "reject" })}>
                          拒绝
                        </Button>
                      </Space>
                    ) : (
                      <Typography.Text type="secondary">仅查看</Typography.Text>
                    )
                  ),
                },
              ]}
            />
          </div>
        )}
      </Card>

      {actionState ? (
        <VersionActionModal
          open
          modalId="admin-reviews-action-modal"
          title={actionState.action === "approve" ? "审核通过" : "拒绝版本"}
          description={actionState.action === "approve" ? "确认通过当前版本审核。" : "请输入拒绝原因。"}
          required={actionState.action === "reject"}
          confirmLoading={actionMutation.isPending}
          errorMessage={actionMutation.error ? (actionMutation.error as Error).message : null}
          onCancel={() => setActionState(null)}
          onSubmit={(comment) => actionMutation.mutate({ versionId: actionState.versionId, action: actionState.action, comment })}
        />
      ) : null}
    </>
  );
}
