/** 组件约定：版本详情页与审核弹窗共用主体；负责查询、展示和动作编排，`variant` 仅区分页面与弹窗，不在此重复推断权限。 */
import { ArrowLeftOutlined, DownloadOutlined } from "@ant-design/icons";
import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Alert, Button, Card, Descriptions, Form, Input, Skeleton, Space, Table, Tag, Typography, message } from "antd";
import dayjs from "dayjs";
import { Link } from "react-router-dom";

import { VersionActionModal } from "./VersionActionModal";
import { ACTION_CONFIG, type UpdateVersionContentInput, type VersionActionKey, type VersionDetailResponse } from "./versionDetailShared";
import { apiRequest } from "../lib/api";
import { formatReviewStatusLabel, reviewStatusTagColor } from "../lib/versionStatusLabels";
import { useVersionPackageDownload } from "../hooks/useVersionPackageDownload";
import { useAuthStore } from "../store/auth";

type AdminVersionDetailPanelProps = {
  versionId: string | null;
  variant?: "page" | "modal";
};

export function AdminVersionDetailPanel({ versionId, variant = "page" }: AdminVersionDetailPanelProps) {
  const accessToken = useAuthStore((state) => state.accessToken);
  const queryClient = useQueryClient();
  const [actionKey, setActionKey] = useState<keyof typeof ACTION_CONFIG | null>(null);
  const { loadingId: downloadingPackageId, download: handleDownloadPackage } = useVersionPackageDownload(accessToken);

  const idPrefix = variant === "modal" ? "admin-reviews-version-detail" : "admin-version-detail";

  const detailQuery = useQuery({
    queryKey: ["admin-version-detail", accessToken, versionId],
    enabled: Boolean(accessToken && versionId),
    queryFn: () => apiRequest<VersionDetailResponse>(`/admin/versions/${versionId}`, { token: accessToken }),
  });

  const updateMutation = useMutation({
    mutationFn: (values: UpdateVersionContentInput) =>
      apiRequest(`/admin/versions/${versionId}`, {
        method: "PATCH",
        token: accessToken,
        body: JSON.stringify(values),
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["admin-version-detail", accessToken, versionId] });
      await queryClient.invalidateQueries({ queryKey: ["admin-review-queue"] });
      message.success("版本文案已保存。");
    },
    onError: (error: Error) => {
      message.error(error.message);
    },
  });

  const actionMutation = useMutation({
    mutationFn: ({ action, comment }: { action: VersionActionKey; comment: string }) =>
      apiRequest(`/admin/versions/${versionId}/${ACTION_CONFIG[action].endpoint}`, {
        method: "POST",
        token: accessToken,
        body: JSON.stringify({ comment }),
      }),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["admin-version-detail", accessToken, versionId] }),
        queryClient.invalidateQueries({ queryKey: ["admin-skill-detail"] }),
        queryClient.invalidateQueries({ queryKey: ["admin-review-queue"] }),
        queryClient.invalidateQueries({ queryKey: ["admin-release-queue"] }),
        queryClient.invalidateQueries({ queryKey: ["admin-review-history"] }),
        queryClient.invalidateQueries({ queryKey: ["public-skills"] }),
      ]);
      message.success(`${ACTION_CONFIG[actionKey ?? "submit"].title}已完成。`);
      setActionKey(null);
    },
    onError: (error: Error) => {
      message.error(error.message);
    },
  });

  const editable = detailQuery.data?.capabilities.edit_content ?? false;

  const availableActions = useMemo(() => {
    const capabilities = detailQuery.data?.capabilities;
    if (!capabilities) {
      return [];
    }
    const actions: VersionActionKey[] = [];
    if (capabilities.submit) {
      actions.push("submit");
    }
    if (capabilities.approve) {
      actions.push("approve", "reject");
    }
    if (capabilities.publish) {
      actions.push("publish");
    }
    if (capabilities.archive) {
      actions.push("archive");
    }
    if (capabilities.rollback) {
      actions.push("rollback");
    }
    return actions;
  }, [detailQuery.data]);

  const initialValues = detailQuery.data
    ? {
        changelog: detailQuery.data.version.changelog,
        install_notes: detailQuery.data.version.install_notes,
        breaking_changes: detailQuery.data.version.breaking_changes,
        readme_markdown: detailQuery.data.version.readme_markdown,
        usage_guide_json: detailQuery.data.version.usage_guide_json,
      }
    : undefined;

  const isMissingVersion = !versionId;

  const rootClass = variant === "modal" ? "admin-version-detail admin-version-detail--modal" : "admin-version-detail";

  return (
    <div className={rootClass}>
      {variant === "page" && detailQuery.data ? (
        <div className="admin-version-detail-back">
          <Link to={`/skills/${detailQuery.data.skill.id}`}>
            <ArrowLeftOutlined />
            <span>返回技能详情</span>
          </Link>
        </div>
      ) : null}
      {isMissingVersion ? <Alert type="warning" showIcon message="缺少版本标识，无法加载版本详情。" /> : null}
      {detailQuery.isError ? <Alert type="error" showIcon message={(detailQuery.error as Error).message} /> : null}
      {detailQuery.isPending ? <Card className="content-card detail-card"><Skeleton active paragraph={{ rows: 8 }} /></Card> : null}
      {!detailQuery.isPending && !detailQuery.data && !isMissingVersion && !detailQuery.isError ? (
        <Alert type="info" showIcon message="当前版本暂无可展示数据。" />
      ) : null}

      {detailQuery.data && !isMissingVersion ? (
        <>
          <Card id={`${idPrefix}-summary-card`} className="content-card detail-card" title={`版本 ${detailQuery.data.version.version}`}>
            <Descriptions column={2}>
              <Descriptions.Item label="所属技能">
                <Link to={`/skills/${detailQuery.data.skill.id}`}>{detailQuery.data.skill.name}</Link>
              </Descriptions.Item>
              <Descriptions.Item label="版本状态">
                <Tag color={reviewStatusTagColor(detailQuery.data.version.review_status)}>{formatReviewStatusLabel(detailQuery.data.version.review_status)}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="分类">{detailQuery.data.skill.category_name}</Descriptions.Item>
              <Descriptions.Item label="发布时间">
                {detailQuery.data.version.published_at ? dayjs(detailQuery.data.version.published_at).format("YYYY-MM-DD HH:mm") : "-"}
              </Descriptions.Item>
            </Descriptions>
            <Space style={{ marginTop: 16 }} wrap>
              {detailQuery.data.capabilities.download_package ? (
                <Button
                  icon={<DownloadOutlined />}
                  loading={Boolean(versionId && downloadingPackageId === versionId)}
                  onClick={() => versionId && void handleDownloadPackage(versionId)}
                >
                  下载 ZIP 包
                </Button>
              ) : null}
              {availableActions.map((action) => (
                <Button key={action} onClick={() => setActionKey(action)}>
                  {ACTION_CONFIG[action].title}
                </Button>
              ))}
              {!availableActions.length && !detailQuery.data.capabilities.download_package ? (
                <Typography.Text type="secondary">当前状态下没有可执行动作。</Typography.Text>
              ) : null}
            </Space>
          </Card>

          <Card id={`${idPrefix}-manifest-card`} className="content-card detail-card" title="Manifest">
            <pre className="code-block">{JSON.stringify(detailQuery.data.version.manifest_json, null, 2)}</pre>
          </Card>

          <Card id={`${idPrefix}-editor-card`} className="content-card detail-card" title="版本文案编辑">
            <div id={`${idPrefix}-editor-form`}>
              <Form layout="vertical" initialValues={initialValues} onFinish={(values) => updateMutation.mutate(values)} disabled={!editable}>
                <Form.Item label="变更说明" name="changelog">
                  <Input.TextArea rows={4} />
                </Form.Item>
                <Form.Item label="安装说明" name="install_notes">
                  <Input.TextArea rows={4} />
                </Form.Item>
                <Form.Item label="破坏性变更" name="breaking_changes">
                  <Input.TextArea rows={3} />
                </Form.Item>
                <Form.Item label="README Markdown" name="readme_markdown">
                  <Input.TextArea rows={12} />
                </Form.Item>
                <Form.Item label="Agent 标准提示词" name={["usage_guide_json", "agent", "standard_prompt"]}>
                  <Input.TextArea rows={5} />
                </Form.Item>
                <Form.Item label="Agent 加速提示词" name={["usage_guide_json", "agent", "accelerated_prompt"]}>
                  <Input.TextArea rows={5} />
                </Form.Item>
                <Form.Item label="Human 标准命令" name={["usage_guide_json", "human", "standard_command"]}>
                  <Input.TextArea rows={3} />
                </Form.Item>
                <Form.Item label="Human 加速命令" name={["usage_guide_json", "human", "accelerated_command"]}>
                  <Input.TextArea rows={3} />
                </Form.Item>
                <Form.Item label="Human 安装后命令" name={["usage_guide_json", "human", "post_install_command"]}>
                  <Input.TextArea rows={4} />
                </Form.Item>
                {updateMutation.error ? <Alert type="error" showIcon message={(updateMutation.error as Error).message} /> : null}
                {!editable ? <Typography.Text type="secondary">当前账号在该版本当前状态下不能编辑版本文案。</Typography.Text> : null}
                <Button type="primary" htmlType="submit" loading={updateMutation.isPending} disabled={!editable}>
                  保存版本文案
                </Button>
              </Form>
            </div>
          </Card>

          <Card id={`${idPrefix}-readme-preview-card`} className="content-card detail-card" title="README 预览">
            <div className="markdown-preview" dangerouslySetInnerHTML={{ __html: detailQuery.data.version.readme_html }} />
          </Card>

          <Card id={`${idPrefix}-review-history-card`} className="content-card" title="审核记录">
            <div id={`${idPrefix}-review-history-table-container`}>
              <Table
                rowKey="id"
                pagination={false}
                dataSource={detailQuery.data.reviews}
                columns={[
                  { title: "动作", dataIndex: "action" },
                  { title: "操作人", dataIndex: "operator_display_name" },
                  { title: "说明", dataIndex: "comment", render: (value: string) => value || "-" },
                  { title: "时间", dataIndex: "created_at", render: (value: string) => dayjs(value).format("YYYY-MM-DD HH:mm") },
                ]}
              />
            </div>
          </Card>
        </>
      ) : null}

      {actionKey ? (
        <VersionActionModal
          open={Boolean(actionKey)}
          modalId={`${idPrefix}-action-modal`}
          title={ACTION_CONFIG[actionKey].title}
          description={ACTION_CONFIG[actionKey].description}
          required={ACTION_CONFIG[actionKey].required}
          confirmLoading={actionMutation.isPending}
          errorMessage={actionMutation.error ? (actionMutation.error as Error).message : null}
          onCancel={() => setActionKey(null)}
          onSubmit={(comment) => actionMutation.mutate({ action: actionKey, comment })}
        />
      ) : null}
    </div>
  );
}
