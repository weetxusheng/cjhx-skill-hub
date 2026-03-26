import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Alert, Button, Card, Descriptions, Form, Input, Space, Table, Tag, Typography } from "antd";
import dayjs from "dayjs";
import { Link, useParams } from "react-router-dom";

import { VersionActionModal } from "../components/VersionActionModal";
import { apiRequest } from "../lib/api";
import { useAuthStore } from "../store/auth";

type VersionDetailResponse = {
  skill: {
    id: string;
    name: string;
    slug: string;
    category_name: string;
    category_slug: string;
    current_published_version_id: string | null;
  };
  version: {
    id: string;
    version: string;
    manifest_json: Record<string, unknown>;
    usage_guide_json: {
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
    readme_markdown: string;
    readme_html: string;
    changelog: string;
    install_notes: string;
    breaking_changes: string;
    source_type: string;
    review_status: string;
    review_comment: string | null;
    published_at: string | null;
    created_at: string;
  };
  reviews: Array<{
    id: string;
    action: string;
    comment: string;
    operator_display_name: string;
    created_at: string;
  }>;
  capabilities: {
    edit_content: boolean;
    submit: boolean;
    approve: boolean;
    reject: boolean;
    publish: boolean;
    archive: boolean;
    rollback: boolean;
  };
};

type ActionConfig = {
  endpoint: string;
  title: string;
  description: string;
  required?: boolean;
};

const ACTION_CONFIG: Record<string, ActionConfig> = {
  submit: { endpoint: "submit", title: "提交审核", description: "可选填写提交说明，提交后版本将进入待审队列。" },
  approve: { endpoint: "approve", title: "审核通过", description: "确认通过当前版本审核，可选填写说明。" },
  reject: { endpoint: "reject", title: "拒绝版本", description: "拒绝原因会记录到审核历史中。", required: true },
  publish: { endpoint: "publish", title: "发布版本", description: "发布后旧的 published 版本会自动归档。" },
  archive: { endpoint: "archive", title: "归档版本", description: "归档后前台将不再展示该版本。", required: false },
  rollback: { endpoint: "rollback", title: "回滚发布", description: "请填写回滚说明，该版本会重新成为当前发布版本。", required: true },
};

export function VersionDetailPage() {
  const { versionId } = useParams();
  const accessToken = useAuthStore((state) => state.accessToken);
  const queryClient = useQueryClient();
  const [actionKey, setActionKey] = useState<keyof typeof ACTION_CONFIG | null>(null);

  const detailQuery = useQuery({
    queryKey: ["admin-version-detail", accessToken, versionId],
    enabled: Boolean(accessToken && versionId),
    queryFn: () => apiRequest<VersionDetailResponse>(`/admin/versions/${versionId}`, { token: accessToken }),
  });

  const updateMutation = useMutation({
    mutationFn: (values: {
      changelog: string;
      install_notes: string;
      breaking_changes: string;
      readme_markdown: string;
      usage_guide_json: {
        agent: { standard_prompt: string; accelerated_prompt: string };
        human: { standard_command: string; accelerated_command: string; post_install_command: string };
      };
    }) =>
      apiRequest(`/admin/versions/${versionId}`, {
        method: "PATCH",
        token: accessToken,
        body: JSON.stringify(values),
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["admin-version-detail", accessToken, versionId] });
    },
  });

  const actionMutation = useMutation({
    mutationFn: ({ action, comment }: { action: keyof typeof ACTION_CONFIG; comment: string }) =>
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
      setActionKey(null);
    },
  });

  const editable = detailQuery.data?.capabilities.edit_content ?? false;

  const availableActions = useMemo(() => {
    const capabilities = detailQuery.data?.capabilities;
    if (!capabilities) {
      return [];
    }
    const actions: Array<keyof typeof ACTION_CONFIG> = [];
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

  return (
    <>
      {detailQuery.isError ? <Alert type="error" showIcon message={(detailQuery.error as Error).message} /> : null}

      {detailQuery.data ? (
        <>
          <Card
            id="admin-version-detail-summary-card"
            className="content-card detail-card"
            title={`版本 ${detailQuery.data.version.version}`}
          >
            <Descriptions column={2}>
              <Descriptions.Item label="所属技能">
                <Link to={`/skills/${detailQuery.data.skill.id}`}>{detailQuery.data.skill.name}</Link>
              </Descriptions.Item>
              <Descriptions.Item label="状态">
                <Tag color={detailQuery.data.version.review_status === "published" ? "green" : "default"}>
                  {detailQuery.data.version.review_status}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="分类">{detailQuery.data.skill.category_name}</Descriptions.Item>
              <Descriptions.Item label="发布时间">
                {detailQuery.data.version.published_at
                  ? dayjs(detailQuery.data.version.published_at).format("YYYY-MM-DD HH:mm")
                  : "-"}
              </Descriptions.Item>
            </Descriptions>
            <Space style={{ marginTop: 16 }} wrap>
              {availableActions.map((action) => (
                <Button key={action} onClick={() => setActionKey(action)}>
                  {ACTION_CONFIG[action].title}
                </Button>
              ))}
              {!availableActions.length ? <Typography.Text type="secondary">当前状态下没有可执行动作。</Typography.Text> : null}
            </Space>
          </Card>

          <Card id="admin-version-detail-manifest-card" className="content-card detail-card" title="Manifest">
            <pre className="code-block">{JSON.stringify(detailQuery.data.version.manifest_json, null, 2)}</pre>
          </Card>

          <Card id="admin-version-detail-editor-card" className="content-card detail-card" title="版本文案编辑">
            <div id="admin-version-detail-editor-form">
              <Form
                layout="vertical"
                initialValues={initialValues}
                onFinish={(values) => updateMutation.mutate(values)}
                disabled={!editable}
              >
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
                {!editable ? (
                  <Typography.Text type="secondary">当前账号在该版本当前状态下不能编辑版本文案。</Typography.Text>
                ) : null}
                <Button type="primary" htmlType="submit" loading={updateMutation.isPending} disabled={!editable}>
                  保存版本文案
                </Button>
              </Form>
            </div>
          </Card>

          <Card id="admin-version-detail-readme-preview-card" className="content-card detail-card" title="README 预览">
            <div className="markdown-preview" dangerouslySetInnerHTML={{ __html: detailQuery.data.version.readme_html }} />
          </Card>

          <Card id="admin-version-detail-review-history-card" className="content-card" title="审核记录">
            <div id="admin-version-detail-review-history-table-container">
              <Table
                rowKey="id"
                pagination={false}
                dataSource={detailQuery.data.reviews}
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
        </>
      ) : null}

      {actionKey ? (
        <VersionActionModal
          open={Boolean(actionKey)}
          modalId="admin-version-detail-action-modal"
          title={ACTION_CONFIG[actionKey].title}
          description={ACTION_CONFIG[actionKey].description}
          required={ACTION_CONFIG[actionKey].required}
          confirmLoading={actionMutation.isPending}
          errorMessage={actionMutation.error ? (actionMutation.error as Error).message : null}
          onCancel={() => setActionKey(null)}
          onSubmit={(comment) => actionMutation.mutate({ action: actionKey, comment })}
        />
      ) : null}
    </>
  );
}
