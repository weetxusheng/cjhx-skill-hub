import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Alert, Button, Card, Space, Table, Tag, Typography, message } from "antd";
import dayjs from "dayjs";

import { ReviewVersionDetailModal } from "../../components/ReviewVersionDetailModal";
import { VersionActionModal } from "../../components/VersionActionModal";
import { apiRequest } from "../../lib/api";
import { formatReviewStatusLabel, reviewStatusTagColor } from "../../lib/versionStatusLabels";
import { hasPermission } from "../../lib/permissions";
import { useAuthStore } from "../../store/auth";
import { ReviewsFiltersCard } from "./_components/ReviewsFiltersCard";

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
  /**
   * 交互约定（审核队列页）：
   * - 加载态：依赖 React Query 默认加载态（表格区域可空，筛选区域可先渲染）。
   * - 错误态：列表请求失败时展示 Alert，不允许静默失败。
   * - 空态：当无待审记录时展示空表格数据（计数为 0）。
   * - 权限不足态：无审核权限时仅允许查看，不展示“通过/拒绝”可执行动作。
   *
   * 数据一致性约束：
   * - 审核动作成功后必须失效审核队列与版本详情缓存，避免详情弹窗与列表状态不一致。
   */
  const accessToken = useAuthStore((state) => state.accessToken);
  const user = useAuthStore((state) => state.user);
  const queryClient = useQueryClient();
  const [actionState, setActionState] = useState<{ versionId: string; action: "approve" | "reject" } | null>(null);
  const [detailVersionId, setDetailVersionId] = useState<string | null>(null);
  const [categoryFilter, setCategoryFilter] = useState<string | undefined>();
  const [creatorDraft, setCreatorDraft] = useState("");
  const [creatorApplied, setCreatorApplied] = useState("");
  const [skillDraft, setSkillDraft] = useState("");
  const [skillApplied, setSkillApplied] = useState("");
  const canReview = hasPermission(user, "skill.review");

  const categoriesQuery = useQuery({
    queryKey: ["admin-review-categories", accessToken],
    queryFn: () => apiRequest<CategoryItem[]>("/admin/categories/options", { token: accessToken }),
  });

  const reviewsQuery = useQuery({
    queryKey: ["admin-review-queue", accessToken, categoryFilter, creatorApplied],
    queryFn: () => {
      const query = new URLSearchParams();
      if (categoryFilter) {
        query.set("category", categoryFilter);
      }
      if (creatorApplied) {
        query.set("created_by", creatorApplied);
      }
      return apiRequest<ReviewItem[]>(`/admin/reviews${query.size ? `?${query.toString()}` : ""}`, { token: accessToken });
    },
  });

  const actionMutation = useMutation({
    /**
     * 审核动作提交方法：
     * - approve/reject 统一走同一 mutation。
     * - 成功后刷新队列与详情数据，并关闭动作弹窗。
     */
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
      message.success(actionState?.action === "approve" ? "审核已通过，版本已进入待发布队列。" : "版本已拒绝，处理意见已保存。");
      setActionState(null);
    },
    onError: (error: Error) => {
      message.error(error.message);
    },
  });

  const filteredReviews = useMemo(() => {
    const list = reviewsQuery.data ?? [];
    const s = skillApplied.toLowerCase();
    if (!s) {
      return list;
    }
    return list.filter((r) =>
      [r.skill_name, r.skill_slug, r.version].some((f) => String(f).toLowerCase().includes(s)),
    );
  }, [reviewsQuery.data, skillApplied]);

  const runSkillSearch = () => {
    setSkillApplied(skillDraft.trim());
  };

  const runCreatorSearch = () => {
    setCreatorApplied(creatorDraft.trim());
  };

  const handleRefreshFilters = () => {
    setCategoryFilter(undefined);
    setSkillDraft("");
    setSkillApplied("");
    setCreatorDraft("");
    setCreatorApplied("");
    void queryClient.invalidateQueries({ queryKey: ["admin-review-queue"] });
  };

  return (
    <>
      <ReviewsFiltersCard
        categoryFilter={categoryFilter}
        onCategoryChange={setCategoryFilter}
        categoryOptions={(categoriesQuery.data ?? []).map((item) => ({ label: item.name, value: item.name }))}
        skillDraft={skillDraft}
        onSkillDraftChange={setSkillDraft}
        onSkillSearch={runSkillSearch}
        creatorDraft={creatorDraft}
        onCreatorDraftChange={setCreatorDraft}
        onCreatorSearch={runCreatorSearch}
        onRefreshFilters={handleRefreshFilters}
        filteredCount={filteredReviews.length}
        apiRowCount={reviewsQuery.data?.length ?? 0}
        skillApplied={skillApplied}
        canReview={canReview}
      />
      <Card id="admin-reviews-table-card" className="content-card">
        {reviewsQuery.isError ? (
          <Alert type="error" showIcon message={(reviewsQuery.error as Error).message} />
        ) : (
          <div id="admin-reviews-table-container">
            <Table
              rowKey="version_id"
              pagination={false}
              dataSource={filteredReviews}
              columns={[
                {
                  title: "技能",
                  dataIndex: "skill_name",
                  render: (_: string, record: ReviewItem) => (
                    <Button type="link" style={{ paddingInline: 0 }} onClick={() => setDetailVersionId(record.version_id)}>
                      {record.skill_name}
                    </Button>
                  ),
                },
                { title: "版本", dataIndex: "version" },
                { title: "分类", dataIndex: "category_name" },
                { title: "提交人", dataIndex: "created_by_display_name" },
                {
                  title: "审核负责人",
                  dataIndex: "assigned_reviewers",
                  render: (value: string[] | null | undefined) => {
                    const items = value ?? [];
                    return items.length ? items.map((item) => <Tag key={item}>{item}</Tag>) : <Typography.Text type="secondary">未配置</Typography.Text>;
                  },
                },
                {
                  title: "最近说明",
                  dataIndex: "latest_review_comment",
                  render: (value: string | null) => value || "-",
                },
                {
                  title: "版本状态",
                  dataIndex: "review_status",
                  render: (value: string) => (
                    <Tag color={reviewStatusTagColor(value)}>{formatReviewStatusLabel(value)}</Tag>
                  ),
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
                  render: (_: unknown, record: ReviewItem) =>
                    canReview ? (
                      <Space size={8}>
                        <Button size="small" onClick={() => setDetailVersionId(record.version_id)}>
                          详情编辑
                        </Button>
                        <Button size="small" onClick={() => setActionState({ versionId: record.version_id, action: "approve" })}>
                          通过
                        </Button>
                        <Button size="small" danger onClick={() => setActionState({ versionId: record.version_id, action: "reject" })}>
                          拒绝
                        </Button>
                      </Space>
                    ) : (
                      <Typography.Text type="secondary">仅查看</Typography.Text>
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

      {detailVersionId ? (
        <ReviewVersionDetailModal
          open={Boolean(detailVersionId)}
          versionId={detailVersionId}
          token={accessToken}
          onClose={() => setDetailVersionId(null)}
        />
      ) : null}
    </>
  );
}
