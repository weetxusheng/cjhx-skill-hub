/**
 * 组件约定：
 * - 前台上传中心抽屉统一承载 ZIP 拖拽上传和“我的上传记录”，不暴露后台版本治理概念。
 * - 打开时读取当前用户自己的上传记录；上传成功后只刷新公共列表和投稿记录。
 */
import { InboxOutlined } from "@ant-design/icons";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Alert, Drawer, Empty, List, Spin, Tag, Typography, Upload, message } from "antd";
import type { UploadChangeParam, UploadFile } from "antd/es/upload/interface";
import dayjs from "dayjs";
import { useState } from "react";

import { apiRequest } from "../lib/api";
import type { PagedResponse, PortalUploadRecordItem } from "../lib/portalTypes";
import { formatReviewStatusLabel, reviewStatusTagColor } from "../lib/versionStatusLabels";

export function PortalUploadCenterDrawer({
  accessToken,
  canUpload,
  open,
  onClose,
}: {
  accessToken: string | null;
  canUpload: boolean;
  open: boolean;
  onClose: () => void;
}) {
  const queryClient = useQueryClient();
  const [uploadFiles, setUploadFiles] = useState<UploadFile[]>([]);

  const recordsQuery = useQuery({
    queryKey: ["portal-upload-records", accessToken],
    enabled: open && Boolean(accessToken),
    queryFn: () =>
      apiRequest<PagedResponse<PortalUploadRecordItem>>("/public/upload-center/records?page=1&page_size=20", {
        token: accessToken,
      }),
  });

  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      if (!accessToken) {
        throw new Error("请先登录后再上传");
      }
      const formData = new FormData();
      formData.append("file", file);
      return apiRequest<{ skill_id: string; version_id: string; created_skill: boolean; review_status: string }>("/admin/skills/upload", {
        method: "POST",
        token: accessToken,
        body: formData,
      });
    },
    onSuccess: async () => {
      setUploadFiles([]);
      message.success("技能包已提交，管理员会继续处理审核与发布。");
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["public-skills"] }),
        queryClient.invalidateQueries({ queryKey: ["portal-upload-records"] }),
      ]);
    },
    onError: (error: Error) => {
      message.error(error.message);
    },
  });

  const handleUploadChange = (info: UploadChangeParam<UploadFile>) => {
    const nextFiles = info.fileList.slice(-1);
    setUploadFiles(nextFiles);
    const file = nextFiles[0]?.originFileObj;
    if (!file) {
      return;
    }
    uploadMutation.reset();
    uploadMutation.mutate(file);
  };

  return (
    <Drawer
      title="前台上传中心"
      width={560}
      open={open}
      onClose={onClose}
      className="portal-upload-drawer"
    >
      <div className="upload-center-shell">
        <div id="portal-upload-center-header" className="upload-center-hero">
          <Typography.Title level={4}>直接提交 ZIP，管理员来处理版本规划</Typography.Title>
          <Typography.Paragraph>
            这里不再要求你判断待审核、待发布或线上版本。你只要上传技能包，下面查看自己的投稿记录，后续由管理员在后台继续审核和发布。
          </Typography.Paragraph>
          <div className="upload-center-hints">
            <span>支持拖拽 ZIP 或点击选择</span>
            <span>根目录必须包含 skill.yaml 与 README.md</span>
            <span>上传后会进入你的投稿记录</span>
            <a href="/downloads/skill-package-demo.zip" download>
              下载示例 ZIP 模板
            </a>
          </div>
        </div>

        <div className="upload-center-dropzone-card">
          {!canUpload ? (
            <Alert
              type="info"
              showIcon
              message="当前账号还没有投稿权限"
              description="请联系管理员开通 skill.upload 权限。权限开通后，这里会直接支持拖拽 ZIP 上传。"
            />
          ) : (
            <>
              <Upload.Dragger
                id="portal-upload-center-dropzone"
                accept=".zip"
                maxCount={1}
                beforeUpload={() => false}
                fileList={uploadFiles}
                className="upload-center-dropzone"
                disabled={uploadMutation.isPending}
                onChange={handleUploadChange}
              >
                <div className="upload-center-dropzone-content">
                  <InboxOutlined className="upload-center-dropzone-icon" />
                  <Typography.Title level={5}>拖拽 ZIP 到这里</Typography.Title>
                  <Typography.Paragraph>
                    或点击选择后立即上传，不再额外弹一次上传窗口。
                  </Typography.Paragraph>
                </div>
              </Upload.Dragger>
              <Typography.Text className="upload-center-record-note">
                {uploadMutation.isPending ? "上传中，请稍候…" : "上传成功后，记录会自动刷新到下面的列表。"}
              </Typography.Text>
              {uploadMutation.error ? (
                <Alert type="error" showIcon message={(uploadMutation.error as Error).message} />
              ) : null}
            </>
          )}
        </div>

        <div id="portal-upload-center-list" className="upload-center-list-card">
          <div className="upload-center-list-head">
            <div>
              <Typography.Text className="results-kicker">我的上传记录</Typography.Text>
              <Typography.Title level={5}>只看自己提交过的技能包</Typography.Title>
            </div>
          </div>

          {recordsQuery.isLoading ? (
            <div className="upload-center-loading">
              <Spin />
            </div>
          ) : recordsQuery.isError ? (
            <Alert type="error" showIcon message={(recordsQuery.error as Error).message} />
          ) : recordsQuery.data?.items.length ? (
            <List
              itemLayout="vertical"
              className="upload-center-list"
              dataSource={recordsQuery.data.items}
              renderItem={(item) => (
                <List.Item key={item.version_id} className="upload-center-item">
                  <div className="upload-center-item-head">
                    <div>
                      <Typography.Title level={5}>{item.skill_name}</Typography.Title>
                      <Typography.Text type="secondary">
                        {item.category_name} · 更新于 {dayjs(item.updated_at).format("YYYY-MM-DD HH:mm")}
                      </Typography.Text>
                    </div>
                    <Tag color={reviewStatusTagColor(item.review_status)}>
                      {formatReviewStatusLabel(item.review_status)}
                    </Tag>
                  </div>
                  <div className="upload-center-item-meta">
                    <span className="upload-center-version">版本 v{item.version}</span>
                    <span>{item.published_at ? `已发布于 ${dayjs(item.published_at).format("YYYY-MM-DD HH:mm")}` : "等待管理员处理"}</span>
                  </div>
                  {item.review_comment ? (
                    <Typography.Paragraph className="upload-center-record-note">
                      最近处理意见：{item.review_comment}
                    </Typography.Paragraph>
                  ) : null}
                </List.Item>
              )}
            />
          ) : (
            <Empty description="还没有上传记录，先拖一个 ZIP 技能包上来。" />
          )}
        </div>
      </div>
    </Drawer>
  );
}
