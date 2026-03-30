/**
 * 组件约定：
 * - 展示技能详情中的收藏与下载明细，遵循管理员可见完整明细、普通运营降级为受限视图。
 * - 明细为空时展示表格空态，不以空白区域代替。
 */
import { Card, Col, Row, Table, Typography } from "antd";
import dayjs from "dayjs";

import type { SkillDownloadRecord, SkillFavoriteRecord } from "../skillDetailTypes";

type SkillEngagementRecordsSectionProps = {
  canViewDownloadDetails: boolean;
  canViewFavoriteDetails: boolean;
  canViewSensitiveDownloadDetails: boolean;
  downloads: SkillDownloadRecord[];
  favorites: SkillFavoriteRecord[];
};

/**
 * 技能详情 - 收藏与下载明细表
 *
 * - `canViewFavoriteDetails` / `canViewDownloadDetails` 为 false 时展示权限不足文案而非空白。
 * - 下载敏感列由 `canViewSensitiveDownloadDetails` 控制；避免无权限用户看到 IP 等字段。
 */
export function SkillEngagementRecordsSection({
  canViewDownloadDetails,
  canViewFavoriteDetails,
  canViewSensitiveDownloadDetails,
  downloads,
  favorites,
}: SkillEngagementRecordsSectionProps) {
  return (
    <section className="detail-layout-section">
      <Row gutter={[16, 16]} className="detail-grid-row">
        <Col xs={24} xl={12} className="detail-grid-col">
          <Card id="admin-skill-detail-favorites-card" className="content-card detail-card detail-card--stretch" title="收藏明细">
            {canViewFavoriteDetails ? (
              <div id="admin-skill-detail-favorites-table-container">
                <Table
                  rowKey={(record) => `${record.user_id}-${record.created_at}`}
                  pagination={{ pageSize: 8 }}
                  dataSource={favorites}
                  columns={[
                    { title: "用户", render: (_value: unknown, record: SkillFavoriteRecord) => `${record.display_name} (${record.username})` },
                    { title: "收藏时间", dataIndex: "created_at", render: (value: string) => dayjs(value).format("YYYY-MM-DD HH:mm") },
                  ]}
                />
              </div>
            ) : (
              <Typography.Text type="secondary">当前账号没有查看收藏明细的权限。</Typography.Text>
            )}
          </Card>
        </Col>
        <Col xs={24} xl={12} className="detail-grid-col">
          <Card id="admin-skill-detail-downloads-card" className="content-card detail-card detail-card--stretch" title="下载明细">
            {canViewDownloadDetails ? (
              <div id="admin-skill-detail-downloads-table-container">
                <Table
                  rowKey="id"
                  pagination={{ pageSize: 8 }}
                  dataSource={downloads}
                  columns={[
                    {
                      title: "用户",
                      render: (_value: unknown, record: SkillDownloadRecord) =>
                        record.display_name ? `${record.display_name} (${record.username ?? "-"})` : "匿名下载（已脱敏）",
                    },
                    { title: "版本", dataIndex: "version" },
                    ...(canViewSensitiveDownloadDetails ? [{ title: "IP", dataIndex: "ip", render: (value: string | null) => value ?? "-" }] : []),
                    { title: "下载时间", dataIndex: "created_at", render: (value: string) => dayjs(value).format("YYYY-MM-DD HH:mm") },
                  ]}
                />
              </div>
            ) : (
              <Typography.Text type="secondary">当前账号没有查看下载明细的权限。</Typography.Text>
            )}
          </Card>
        </Col>
      </Row>
    </section>
  );
}
