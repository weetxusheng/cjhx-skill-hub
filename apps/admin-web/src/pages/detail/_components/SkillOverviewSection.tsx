/**
 * 组件约定：
 * - 展示技能主档摘要、编辑表单和上传入口，是技能详情页的首屏操作区。
 * - `canManageSkill` / `canUploadVersion` 决定表单和按钮是否可操作，禁止在组件内部重新推断权限。
 */
import { Alert, Button, Card, Col, Descriptions, Form, Input, Row, Select, Tag, Typography } from "antd";
import dayjs from "dayjs";

import { formatReviewStatusLabel, reviewStatusTagColor } from "../../../lib/versionStatusLabels";
import type { CategoryItem, SkillDetailResponse, SkillUpdateInput } from "../skillDetailTypes";

type SkillOverviewSectionProps = {
  categories: CategoryItem[];
  canManageSkill: boolean;
  canUploadVersion: boolean;
  detail: SkillDetailResponse;
  errorMessage: string | null;
  initialValues: SkillUpdateInput | undefined;
  isSaving: boolean;
  onOpenUpload: () => void;
  onSubmit: (values: SkillUpdateInput) => void;
};

/**
 * 技能详情 - 主档信息与可编辑表单、上传入口
 *
 * - `canManageSkill` 为 false 时表单只读或隐藏保存；`canUploadVersion` 控制上传按钮。
 * - `errorMessage` / `isSaving` 用于表单级错误与提交中状态。
 */
export function SkillOverviewSection({
  categories,
  canManageSkill,
  canUploadVersion,
  detail,
  errorMessage,
  initialValues,
  isSaving,
  onOpenUpload,
  onSubmit,
}: SkillOverviewSectionProps) {
  return (
    <section className="detail-layout-section">
      <Row gutter={[16, 16]} className="detail-grid-row">
        <Col xs={24} xl={14} className="detail-grid-col">
          <Card id="admin-skill-detail-main-info-card" className="content-card detail-card" title="主档信息">
            <div className="detail-card-stack">
              <Descriptions column={2} className="detail-descriptions">
                <Descriptions.Item label="名称">{detail.skill.name}</Descriptions.Item>
                <Descriptions.Item label="Slug">{detail.skill.slug}</Descriptions.Item>
                <Descriptions.Item label="分类">{detail.skill.category_name}</Descriptions.Item>
                <Descriptions.Item label="状态">
                  <Tag color={detail.skill.status === "active" ? "green" : "default"}>{detail.skill.status}</Tag>
                </Descriptions.Item>
                <Descriptions.Item label="负责人">{detail.skill.owner_display_name ?? "-"}</Descriptions.Item>
                <Descriptions.Item label="当前线上版本">{detail.current_published_version ? `v${detail.current_published_version}` : "未发布"}</Descriptions.Item>
                <Descriptions.Item label="最新版本状态">
                  <Tag
                    color={
                      detail.latest_version_status ? reviewStatusTagColor(detail.latest_version_status) : "default"
                    }
                  >
                    {formatReviewStatusLabel(detail.latest_version_status)}
                  </Tag>
                </Descriptions.Item>
                <Descriptions.Item label="发布时间">
                  {detail.skill.published_at ? dayjs(detail.skill.published_at).format("YYYY-MM-DD HH:mm") : "-"}
                </Descriptions.Item>
                <Descriptions.Item label="待审核">{detail.pending_review_count}</Descriptions.Item>
                <Descriptions.Item label="待发布">{detail.pending_release_count}</Descriptions.Item>
                <Descriptions.Item label="下载量">{detail.skill.download_count}</Descriptions.Item>
                <Descriptions.Item label="收藏量">{detail.skill.favorite_count}</Descriptions.Item>
                <Descriptions.Item label="点赞量">{detail.skill.like_count}</Descriptions.Item>
              </Descriptions>
              <div className="detail-card-footer">
                {canUploadVersion ? (
                  <Button type="primary" onClick={onOpenUpload}>
                    上传新版本
                  </Button>
                ) : (
                  <Typography.Text type="secondary">当前账号对该技能没有上传新版本权限。</Typography.Text>
                )}
              </div>
            </div>
          </Card>
        </Col>
        <Col xs={24} xl={10} className="detail-grid-col">
          <Card id="admin-skill-detail-editor-card" className="content-card detail-card" title="编辑展示信息">
            <div id="admin-skill-detail-editor-form">
              <Form layout="vertical" initialValues={initialValues} onFinish={onSubmit} disabled={!canManageSkill} className="detail-form-shell">
                <Form.Item label="名称" name="name" rules={[{ required: true }]}>
                  <Input />
                </Form.Item>
                <Form.Item label="摘要" name="summary" rules={[{ required: true }]}>
                  <Input.TextArea rows={3} />
                </Form.Item>
                <Form.Item label="详细描述" name="description" rules={[{ required: true }]}>
                  <Input.TextArea rows={5} />
                </Form.Item>
                <Form.Item label="分类" name="category_slug" rules={[{ required: true }]}>
                  <Select options={categories.map((item) => ({ label: item.name, value: item.slug }))} />
                </Form.Item>
                <div className="detail-card-footer">
                  {errorMessage ? <Alert type="error" showIcon message={errorMessage} /> : null}
                  {!canManageSkill ? <Typography.Text type="secondary">当前账号对该技能只有只读权限，不能修改主档信息。</Typography.Text> : null}
                  <Button type="primary" htmlType="submit" loading={isSaving} disabled={!canManageSkill}>
                    保存主档
                  </Button>
                </div>
              </Form>
            </div>
          </Card>
        </Col>
      </Row>
    </section>
  );
}
