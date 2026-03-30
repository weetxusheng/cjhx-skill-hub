/**
 * 组件约定：
 * - 后台技能详情内上传新版本统一走此弹窗，上传成功后由外层决定跳转或刷新。
 * - 只接受 ZIP 并通过统一上传接口提交，不在前端推断版本规划逻辑。
 */
import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Alert, Modal, Typography, Upload, message } from "antd";
import type { UploadFile } from "antd/es/upload/interface";

import { apiRequest } from "../lib/api";

type SkillUploadModalProps = {
  open: boolean;
  token: string | null;
  onClose: () => void;
  onSuccess: (payload: { skill_id: string; version_id: string; created_skill: boolean }) => void;
  modalId?: string;
};

type UploadResponse = {
  skill_id: string;
  version_id: string;
  created_skill: boolean;
  review_status: string;
  parsed_manifest: Record<string, unknown>;
};

export function SkillUploadModal({ open, token, onClose, onSuccess, modalId }: SkillUploadModalProps) {
  const [fileList, setFileList] = useState<UploadFile[]>([]);

  const uploadMutation = useMutation({
    mutationFn: async () => {
      const file = fileList[0]?.originFileObj;
      if (!file) {
        throw new Error("请先选择一个 ZIP 技能包");
      }
      const formData = new FormData();
      formData.append("file", file);
      return apiRequest<UploadResponse>("/admin/skills/upload", {
        method: "POST",
        token,
        body: formData,
      });
    },
    onSuccess: (payload) => {
      message.success(
        payload.created_skill ? "技能包已上传，技能主档已创建，版本已进入待审核。" : "新版本已上传，已进入待审核。",
      );
      setFileList([]);
      onSuccess(payload);
      onClose();
    },
    onError: (error: Error) => {
      message.error(error.message);
    },
  });

  return (
    <Modal
      title="上传技能包"
      open={open}
      onCancel={() => {
        setFileList([]);
        uploadMutation.reset();
        onClose();
      }}
      onOk={() => uploadMutation.mutate()}
      confirmLoading={uploadMutation.isPending}
      okText="开始上传"
      wrapProps={modalId ? { id: modalId } : undefined}
    >
      <Typography.Paragraph>
        只支持根目录包含 <code>skill.yaml</code> 和 <code>README.md</code> 的 ZIP 技能包。{" "}
        <a href="/downloads/skill-package-demo.zip" download>
          下载示例 ZIP
        </a>
      </Typography.Paragraph>
      <Upload.Dragger
        accept=".zip"
        maxCount={1}
        beforeUpload={() => false}
        fileList={fileList}
        onChange={({ fileList: next }) => setFileList(next)}
      >
        <p className="ant-upload-text">点击或拖拽上传技能 ZIP 包</p>
      </Upload.Dragger>
      {uploadMutation.error ? <Alert type="error" showIcon message={(uploadMutation.error as Error).message} /> : null}
    </Modal>
  );
}
