/**
 * 组件约定：
 * - 汇总技能详情中的版本时间线和最近审核记录，是导航到版本详情的主要入口之一。
 * - 只展示接口已给出的版本和审核摘要，不在前端补推断额外状态。
 * - 操作列「下载 ZIP」走与版本详情相同的鉴权下载接口，失败时由全局 message 提示。
 */
import { DownloadOutlined } from "@ant-design/icons";
import { Button, Card, Table, Tag } from "antd";
import dayjs from "dayjs";
import { Link } from "react-router-dom";

import { formatReviewStatusLabel, reviewStatusTagColor } from "../../../lib/versionStatusLabels";
import { useVersionPackageDownload } from "../../../hooks/useVersionPackageDownload";
import { useAuthStore } from "../../../store/auth";
import type { ReviewRecordItem, SkillVersionSummary } from "../skillDetailTypes";

type SkillTimelineSectionProps = {
  recentReviews: ReviewRecordItem[];
  versions: SkillVersionSummary[];
};

/**
 * 技能详情 - 版本时间线与近期审核记录
 *
 * - 版本行链接到 `/versions/:id`；审核表展示最近记录，具体条数由接口决定。
 */
export function SkillTimelineSection({ recentReviews, versions }: SkillTimelineSectionProps) {
  const accessToken = useAuthStore((state) => state.accessToken);
  const { loadingId, download } = useVersionPackageDownload(accessToken);

  return (
    <>
      <section className="detail-layout-section">
        <Card id="admin-skill-detail-versions-card" className="content-card" title="版本时间线">
          <div id="admin-skill-detail-versions-table-container">
            <Table
              rowKey="id"
              pagination={false}
              dataSource={versions}
              columns={[
                {
                  title: "版本",
                  dataIndex: "version",
                  render: (_value: string, record: SkillVersionSummary) => <Link to={`/versions/${record.id}`}>{record.version}</Link>,
                },
                {
                  title: "版本状态",
                  dataIndex: "review_status",
                  render: (value: string) => (
                    <Tag color={reviewStatusTagColor(value)}>{formatReviewStatusLabel(value)}</Tag>
                  ),
                },
                { title: "创建时间", dataIndex: "created_at", render: (value: string) => dayjs(value).format("YYYY-MM-DD HH:mm") },
                {
                  title: "发布时间",
                  dataIndex: "published_at",
                  render: (value: string | null) => (value ? dayjs(value).format("YYYY-MM-DD HH:mm") : "-"),
                },
                {
                  title: "操作",
                  key: "actions",
                  width: 120,
                  render: (_: unknown, record: SkillVersionSummary) => (
                    <Button
                      type="link"
                      size="small"
                      icon={<DownloadOutlined />}
                      loading={loadingId === record.id}
                      onClick={() => void download(record.id)}
                    >
                      下载 ZIP
                    </Button>
                  ),
                },
              ]}
            />
          </div>
        </Card>
      </section>

      <section className="detail-layout-section">
        <Card id="admin-skill-detail-recent-audit-card" className="content-card" title="最近审核记录">
          <div id="admin-skill-detail-recent-audit-table-container">
            <Table
              rowKey="id"
              pagination={false}
              dataSource={recentReviews}
              columns={[
                { title: "动作", dataIndex: "action" },
                { title: "操作人", dataIndex: "operator_display_name" },
                { title: "说明", dataIndex: "comment", render: (value: string) => value || "-" },
                { title: "时间", dataIndex: "created_at", render: (value: string) => dayjs(value).format("YYYY-MM-DD HH:mm") },
              ]}
            />
          </div>
        </Card>
      </section>
    </>
  );
}
