/**
 * 组件约定：
 * - 审核中心内联查看版本详情时复用此弹窗，不跳离当前待审上下文。
 * - 仅负责展示、审核通过/拒绝动作和反馈，不承担待审列表刷新策略之外的导航逻辑。
 */
import { DownloadOutlined } from "@ant-design/icons";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Alert, Button, Descriptions, Form, Input, Modal, Space, Table, Tag, Typography, message } from "antd";
import dayjs from "dayjs";

import { apiRequest, downloadBinary } from "../lib/api";
import { formatReviewStatusLabel, reviewStatusTagColor } from "../lib/versionStatusLabels";

type VersionDetailResponse = {
  skill: {
    id: string;
    name: string;
    slug: string;
    category_name: string;
  };
  version: {
    id: string;
    version: string;
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
    review_status: string;
    published_at: string | null;
  };
  reviews: Array<{
    id: string;
    action: string;
    comment: string;
    operator_display_name: string;
    created_at: string;
  }>;
};

type ReviewVersionDetailModalProps = {
  open: boolean;
  versionId: string;
  token: string | null;
  onClose: () => void;
};

export function ReviewVersionDetailModal({ open, versionId, token, onClose }: ReviewVersionDetailModalProps) {
  const queryClient = useQueryClient();
  const [downloadingPackage, setDownloadingPackage] = useState(false);

  const detailQuery = useQuery({
    queryKey: ["admin-review-version-detail", token, versionId],
    enabled: open && Boolean(token && versionId),
    queryFn: () => apiRequest<VersionDetailResponse>(`/admin/versions/${versionId}`, { token }),
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
        token,
        body: JSON.stringify(values),
      }),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["admin-review-version-detail", token, versionId] }),
        queryClient.invalidateQueries({ queryKey: ["admin-version-detail"] }),
        queryClient.invalidateQueries({ queryKey: ["admin-review-queue"] }),
      ]);
      message.success("审核详情中的版本文案已保存。");
    },
    onError: (error: Error) => {
      message.error(error.message);
    },
  });

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
    <Modal
      open={open}
      onCancel={onClose}
      footer={null}
      width={980}
      title="审核详情"
      destroyOnClose
      wrapProps={{ id: "admin-reviews-version-detail-modal" }}
    >
      {detailQuery.isError ? <Alert type="error" showIcon message={(detailQuery.error as Error).message} /> : null}

      {detailQuery.data ? (
        <Space direction="vertical" size={16} style={{ width: "100%" }}>
          <Descriptions bordered size="small" column={2}>
            <Descriptions.Item label="技能">{detailQuery.data.skill.name}</Descriptions.Item>
            <Descriptions.Item label="版本">v{detailQuery.data.version.version}</Descriptions.Item>
            <Descriptions.Item label="分类">{detailQuery.data.skill.category_name}</Descriptions.Item>
            <Descriptions.Item label="版本状态">
              <Tag color={reviewStatusTagColor(detailQuery.data.version.review_status)}>
                {formatReviewStatusLabel(detailQuery.data.version.review_status)}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="发布时间">
              {detailQuery.data.version.published_at ? dayjs(detailQuery.data.version.published_at).format("YYYY-MM-DD HH:mm") : "-"}
            </Descriptions.Item>
            <Descriptions.Item label="Slug">{detailQuery.data.skill.slug}</Descriptions.Item>
          </Descriptions>

          {token && versionId ? (
            <div>
              <Button
                icon={<DownloadOutlined />}
                loading={downloadingPackage}
                onClick={async () => {
                  setDownloadingPackage(true);
                  try {
                    await downloadBinary(`/admin/versions/${versionId}/package`, token);
                    message.success("已开始下载技能包。");
                  } catch (error) {
                    message.error((error as Error).message);
                  } finally {
                    setDownloadingPackage(false);
                  }
                }}
              >
                下载 ZIP 包
              </Button>
            </div>
          ) : null}

          <div id="admin-reviews-version-detail-form">
            <Form layout="vertical" initialValues={initialValues} onFinish={(values) => updateMutation.mutate(values)}>
              <Form.Item label="变更说明" name="changelog">
                <Input.TextArea rows={3} />
              </Form.Item>
              <Form.Item label="安装说明" name="install_notes">
                <Input.TextArea rows={3} />
              </Form.Item>
              <Form.Item label="破坏性变更" name="breaking_changes">
                <Input.TextArea rows={3} />
              </Form.Item>
              <Form.Item label="README Markdown" name="readme_markdown">
                <Input.TextArea rows={10} />
              </Form.Item>
              <Form.Item label="Agent 标准提示词" name={["usage_guide_json", "agent", "standard_prompt"]}>
                <Input.TextArea rows={4} />
              </Form.Item>
              <Form.Item label="Agent 加速提示词" name={["usage_guide_json", "agent", "accelerated_prompt"]}>
                <Input.TextArea rows={4} />
              </Form.Item>
              <Form.Item label="Human 标准命令" name={["usage_guide_json", "human", "standard_command"]}>
                <Input.TextArea rows={2} />
              </Form.Item>
              <Form.Item label="Human 加速命令" name={["usage_guide_json", "human", "accelerated_command"]}>
                <Input.TextArea rows={2} />
              </Form.Item>
              <Form.Item label="Human 安装后命令" name={["usage_guide_json", "human", "post_install_command"]}>
                <Input.TextArea rows={3} />
              </Form.Item>
              {updateMutation.error ? <Alert type="error" showIcon message={(updateMutation.error as Error).message} /> : null}
              <Button type="primary" htmlType="submit" loading={updateMutation.isPending}>
                保存版本文案
              </Button>
            </Form>
          </div>

          <div id="admin-reviews-version-detail-history-table">
            <Table
              rowKey="id"
              pagination={false}
              size="small"
              dataSource={detailQuery.data.reviews}
              columns={[
                { title: "动作", dataIndex: "action" },
                { title: "操作人", dataIndex: "operator_display_name" },
                { title: "说明", dataIndex: "comment", render: (value: string) => value || "-" },
                { title: "时间", dataIndex: "created_at", render: (value: string) => dayjs(value).format("YYYY-MM-DD HH:mm") },
              ]}
            />
          </div>
        </Space>
      ) : detailQuery.isLoading ? (
        <Typography.Text type="secondary">加载中...</Typography.Text>
      ) : null}
    </Modal>
  );
}
