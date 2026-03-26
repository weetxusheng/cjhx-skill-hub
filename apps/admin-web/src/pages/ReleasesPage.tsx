import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Alert, Button, Card, Space, Table, Tag, Typography } from "antd";
import dayjs from "dayjs";
import { Link } from "react-router-dom";

import { VersionActionModal } from "../components/VersionActionModal";
import { apiRequest } from "../lib/api";
import { useAuthStore } from "../store/auth";

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
  const accessToken = useAuthStore((state) => state.accessToken);
  const queryClient = useQueryClient();
  const [publishingVersionId, setPublishingVersionId] = useState<string | null>(null);

  const releasesQuery = useQuery({
    queryKey: ["admin-release-queue", accessToken],
    queryFn: () => apiRequest<PendingReleaseItem[]>("/admin/releases/pending", { token: accessToken }),
  });

  const publishMutation = useMutation({
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
      setPublishingVersionId(null);
    },
  });

  return (
    <>
      <Card id="admin-releases-table-card" className="content-card">
        {releasesQuery.isError ? (
          <Alert type="error" showIcon message={(releasesQuery.error as Error).message} />
        ) : (
          <div id="admin-releases-table-container">
            <Table
              rowKey="version_id"
              pagination={false}
              dataSource={releasesQuery.data ?? []}
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
                    return items.length
                      ? items.map((item) => <Tag key={item}>{item}</Tag>)
                      : <Typography.Text type="secondary">未配置</Typography.Text>;
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
