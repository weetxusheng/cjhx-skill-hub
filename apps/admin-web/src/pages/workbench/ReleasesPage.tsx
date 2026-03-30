import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Alert, Button, Card, Empty, Select, Space, Table, Tag, Typography, message } from "antd";
import dayjs from "dayjs";
import { Link } from "react-router-dom";

import { AdminFiltersRefreshButton, AdminKeywordSearchCompact } from "../../components/AdminListToolbar";
import { VersionActionModal } from "../../components/VersionActionModal";
import { apiRequest } from "../../lib/api";
import { useAuthStore } from "../../store/auth";

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
  assigned_publishers: string[];
};

export function ReleasesPage() {
  /**
   * 交互约定（待发布队列页）：
   * - 错误态：队列请求失败时展示 Alert。
   * - 空态：无待发布版本时展示空表格数据。
   * - 操作态：点击“发布”后弹出确认框；提交中按钮 loading，避免重复发布。
   *
   * 状态一致性约束：
   * - 发布成功后必须同时刷新待发布、待审核、技能列表、技能详情与版本详情，
   *   保证“发布后自动归档旧版本”的链路在所有页面立即可见。
   */
  const accessToken = useAuthStore((state) => state.accessToken);
  const queryClient = useQueryClient();
  const [publishingVersionId, setPublishingVersionId] = useState<string | null>(null);
  const [keywordDraft, setKeywordDraft] = useState("");
  const [keywordApplied, setKeywordApplied] = useState("");
  const [categoryFilter, setCategoryFilter] = useState<string | undefined>();

  const releasesQuery = useQuery({
    queryKey: ["admin-release-queue", accessToken],
    queryFn: () => apiRequest<PendingReleaseItem[]>("/admin/releases/pending", { token: accessToken }),
  });

  const publishMutation = useMutation({
    /**
     * 发布动作提交方法：
     * - 通过版本发布接口触发状态迁移。
     * - 成功后关闭弹窗并刷新关键查询缓存。
     */
    mutationFn: ({ versionId, comment }: { versionId: string; comment: string }) =>
      apiRequest(`/admin/versions/${versionId}/publish`, {
        method: "POST",
        token: accessToken,
        body: JSON.stringify({ comment }),
      }),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["admin-release-queue"] }),
        queryClient.invalidateQueries({ queryKey: ["admin-review-queue"] }),
        queryClient.invalidateQueries({ queryKey: ["admin-skill-list"] }),
        queryClient.invalidateQueries({ queryKey: ["admin-skill-detail"] }),
        queryClient.invalidateQueries({ queryKey: ["admin-version-detail"] }),
      ]);
      message.success("版本已发布，旧线上版本已按规则归档。");
      setPublishingVersionId(null);
    },
    onError: (error: Error) => {
      message.error(error.message);
    },
  });

  const categoryOptions = useMemo(() => {
    const names = [...new Set((releasesQuery.data ?? []).map((r) => r.category_name))].sort();
    return names.map((name) => ({ label: name, value: name }));
  }, [releasesQuery.data]);

  const filteredReleases = useMemo(() => {
    let list = releasesQuery.data ?? [];
    if (categoryFilter) {
      list = list.filter((r) => r.category_name === categoryFilter);
    }
    const s = keywordApplied.toLowerCase();
    if (s) {
      list = list.filter((r) =>
        [r.skill_name, r.skill_slug, r.version, r.created_by_display_name, r.category_name].some((f) =>
          String(f).toLowerCase().includes(s),
        ),
      );
    }
    return list;
  }, [releasesQuery.data, categoryFilter, keywordApplied]);

  const runKeywordSearch = () => {
    setKeywordApplied(keywordDraft.trim());
  };

  const handleRefreshFilters = () => {
    setKeywordDraft("");
    setKeywordApplied("");
    setCategoryFilter(undefined);
    void queryClient.invalidateQueries({ queryKey: ["admin-release-queue"] });
  };

  return (
    <>
      <Card id="admin-releases-filters-card" className="content-card filters-card">
        <div className="admin-list-toolbar">
          <div className="admin-list-toolbar__filters">
            <AdminKeywordSearchCompact
              value={keywordDraft}
              onChange={setKeywordDraft}
              onSearch={runKeywordSearch}
              placeholder="搜索技能名、slug、版本号、提交人或分类"
            />
            <Select
              allowClear
              className="filters-select"
              placeholder="全部分类"
              value={categoryFilter}
              onChange={setCategoryFilter}
              options={categoryOptions}
            />
            <AdminFiltersRefreshButton onClick={handleRefreshFilters} />
            <Typography.Text type="secondary">共 {filteredReleases.length} 条</Typography.Text>
          </div>
        </div>
      </Card>

      <Card id="admin-releases-table-card" className="content-card">
        {releasesQuery.isError ? (
          <Alert type="error" showIcon message={(releasesQuery.error as Error).message} />
        ) : (releasesQuery.data?.length ?? 0) === 0 ? (
          <Empty description="当前没有待发布版本" />
        ) : filteredReleases.length === 0 ? (
          <Empty description="没有匹配当前筛选的待发布版本" />
        ) : (
          <div id="admin-releases-table-container">
            <Table
              rowKey="version_id"
              pagination={false}
              dataSource={filteredReleases}
              columns={[
                {
                  title: "技能 / 版本",
                  render: (_: unknown, record: PendingReleaseItem) => (
                    <Space direction="vertical" size={0}>
                      <Link to={`/versions/${record.version_id}`}>{record.skill_name}</Link>
                      <Typography.Text type="secondary">
                        {record.skill_slug} · v{record.version}
                      </Typography.Text>
                    </Space>
                  ),
                },
                { title: "分类", dataIndex: "category_name" },
                { title: "提交人", dataIndex: "created_by_display_name" },
                {
                  title: "最近审核意见",
                  dataIndex: "latest_review_comment",
                  render: (value: string | null) => value || "-",
                },
                {
                  title: "已通过时间",
                  dataIndex: "approved_at",
                  render: (value: string | null) => (value ? dayjs(value).format("YYYY-MM-DD HH:mm") : "-"),
                },
                {
                  title: "发布负责人",
                  dataIndex: "assigned_publishers",
                  render: (value: string[] | null | undefined) => {
                    const items = value ?? [];
                    return items.length ? items.map((item) => <Tag key={item}>{item}</Tag>) : <Typography.Text type="secondary">未配置</Typography.Text>;
                  },
                },
                {
                  title: "操作",
                  render: (_: unknown, record: PendingReleaseItem) => (
                    <Button type="primary" size="small" onClick={() => setPublishingVersionId(record.version_id)}>
                      发布
                    </Button>
                  ),
                },
              ]}
            />
          </div>
        )}
      </Card>

      {publishingVersionId ? (
        <VersionActionModal
          open
          modalId="admin-releases-publish-modal"
          title="发布版本"
          description="发布后，当前线上已发布版本会自动归档。"
          confirmLoading={publishMutation.isPending}
          errorMessage={publishMutation.error ? (publishMutation.error as Error).message : null}
          onCancel={() => setPublishingVersionId(null)}
          onSubmit={(comment) => publishMutation.mutate({ versionId: publishingVersionId, comment })}
        />
      ) : null}
    </>
  );
}
