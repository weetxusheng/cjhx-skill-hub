/**
 * 组件约定：
 * - 统一承载提交审核、通过、拒绝、发布、归档、回滚等动作的确认输入弹窗。
 * - 是否必填说明由 `required` 控制；真正动作语义与状态机校验由调用方决定。
 */
import { useState } from "react";
import { Alert, Input, Modal, Typography } from "antd";

type VersionActionModalProps = {
  open: boolean;
  title: string;
  description: string;
  required?: boolean;
  confirmLoading?: boolean;
  errorMessage?: string | null;
  defaultComment?: string;
  modalId?: string;
  onCancel: () => void;
  onSubmit: (comment: string) => void;
};

export function VersionActionModal({
  open,
  title,
  description,
  required = false,
  confirmLoading = false,
  errorMessage,
  defaultComment = "",
  modalId,
  onCancel,
  onSubmit,
}: VersionActionModalProps) {
  const [comment, setComment] = useState(defaultComment);

  return (
    <Modal
      title={title}
      open={open}
      onCancel={onCancel}
      onOk={() => onSubmit(comment)}
      confirmLoading={confirmLoading}
      okButtonProps={{ disabled: required && !comment.trim() }}
      okText="确认"
      wrapProps={modalId ? { id: modalId } : undefined}
    >
      <Typography.Paragraph>{description}</Typography.Paragraph>
      <Input.TextArea
        rows={4}
        placeholder={required ? "请输入说明" : "可选填写说明"}
        value={comment}
        onChange={(event) => setComment(event.target.value)}
      />
      {errorMessage ? <Alert type="error" showIcon message={errorMessage} style={{ marginTop: 16 }} /> : null}
    </Modal>
  );
}
