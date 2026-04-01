/**
 * 组件约定：
 * - 前台上传中心抽屉统一承载 ZIP 拖拽上传和“我的上传记录”，不暴露后台版本治理概念。
 * - 打开时读取当前用户自己的上传记录；无投稿权限时额外查询可联系的系统角色人员。
 * - 上传成功后只刷新公共列表和投稿记录。
 */
import { InboxOutlined } from "@ant-design/icons";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Alert, Drawer, Empty, List, Spin, Tag, Typography, Upload, message } from "antd";
import type { UploadChangeParam, UploadFile } from "antd/es/upload/interface";
import dayjs from "dayjs";
import { useState } from "react";

import { apiRequest } from "../lib/api";
import type { PagedResponse, PortalUploadRecordItem, SystemRoleContactsResponse } from "../lib/portalTypes";
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

  const systemRoleContactsQuery = useQuery({
    queryKey: ["system-role-contacts", accessToken, "admin"],
    enabled: open && Boolean(accessToken) && !canUpload,
    queryFn: () =>
      apiRequest<SystemRoleContactsResponse>("/public/system-role-contacts?role_code=admin", {
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

  const adminContacts = systemRoleContactsQuery.data?.items ?? [];
  const adminContactNames = adminContacts.map((item) => item.display_name).join(", ");

  return (
    <Drawer
      title="技能上传"
      width={560}
      open={open}
      onClose={onClose}
      className="portal-upload-drawer"
    >
      <div className="upload-center-shell">
        <div id="portal-upload-center-header" className="upload-center-hero">
          <Typography.Title level={4}>上传技能包，查看投稿进度</Typography.Title>
          <Typography.Paragraph>
            用于提交技能 ZIP，并集中查看你的投稿记录与处理结果。审核、发布等后续流程由平台统一处理。
          </Typography.Paragraph>
          <div className="upload-center-hints">
            <span>支持 ZIP 上传</span>
            <span>需包含 skill.yaml 与 README.md</span>
            <span>可查看投稿进度</span>
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
              description={
                <div id="portal-upload-center-forbidden" className="upload-center-forbidden">
                  <Typography.Paragraph>
                    请联系管理员（{adminContactNames}）开通 skill.upload 权限。权限开通后，请在这里上传技能 ZIP （支持拖拽）。
                  </Typography.Paragraph>
                </div>
              }
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
                  <Typography.Title level={5}>技能包上传</Typography.Title>
                  <Typography.Paragraph>
                    拖拽 ZIP 或点击选择后立即上传
                  </Typography.Paragraph>
                </div>
              </Upload.Dragger>
              <Typography.Text className="upload-center-record-note">
                {uploadMutation.isPending ? "上传中，请稍候…" : ""}
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
              <Typography.Title level={5} className="results-kicker">我的上传记录</Typography.Title>
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
            <Empty description={canUpload ? "还没有上传记录，先拖一个 ZIP 技能包上来。" : "当前账号暂无可查看的投稿记录。"} />
          )}
        </div>
      </div>
    </Drawer>
  );
}
