/**
 * 组件约定：
 * - 负责展示点赞、收藏、下载的聚合统计与 7/30 天趋势，不直接请求数据。
 * - 时间窗口切换通过 `onStatsWindowChange` 上抛，保持组件只读和可复用。
 */
import { Card, Progress, Segmented, Space, Table, Typography } from "antd";

import type { SkillStatsOverview } from "../skillDetailTypes";

type SkillStatsCardProps = {
  stats: SkillStatsOverview | undefined;
  statsWindow: "7" | "30";
  onStatsWindowChange: (value: "7" | "30") => void;
};

/**
 * 技能详情 - 点赞/收藏/下载汇总与近期趋势
 *
 * - 无 `stats` 时展示「暂无统计数据」占位。
 * - `statsWindow` 切换时父组件应重新请求对应窗口的序列数据（由页面层 query 绑定）。
 */
export function SkillStatsCard({ stats, statsWindow, onStatsWindowChange }: SkillStatsCardProps) {
  if (!stats) {
    return (
      <Card id="admin-skill-detail-stats-card" className="content-card detail-card detail-card--stretch" title="数据统计">
        <Typography.Text type="secondary">暂无统计数据。</Typography.Text>
      </Card>
    );
  }

  const statsDays = Number(statsWindow);
  const statsCards = [
    { label: "点赞", value: stats.like_count, color: "#c2185b" },
    { label: "收藏", value: stats.favorite_count, color: "#b26a00" },
    { label: "下载", value: stats.download_count, color: "#237804" },
  ];
  const trendRows = [
    { key: "likes", label: "点赞", points: stats.recent_likes.slice(0, statsDays) },
    { key: "favorites", label: "收藏", points: stats.recent_favorites.slice(0, statsDays) },
    { key: "downloads", label: "下载", points: stats.recent_downloads.slice(0, statsDays) },
  ];

  return (
    <Card id="admin-skill-detail-stats-card" className="content-card detail-card detail-card--stretch" title="数据统计">
      <Space direction="vertical" size={12} style={{ width: "100%" }}>
        <Space wrap>
          {statsCards.map((item) => (
            <Card key={item.label} size="small" style={{ minWidth: 110 }}>
              <Typography.Text type="secondary">{item.label}</Typography.Text>
              <Typography.Title level={4} style={{ margin: "8px 0 0", color: item.color }}>
                {item.value}
              </Typography.Title>
            </Card>
          ))}
        </Space>
        <Space align="center" wrap>
          <Typography.Text strong>趋势窗口</Typography.Text>
          <Segmented
            value={statsWindow}
            onChange={(value) => onStatsWindowChange(value as "7" | "30")}
            options={[
              { label: "最近 7 天", value: "7" },
              { label: "最近 30 天", value: "30" },
            ]}
          />
        </Space>
        <div id="admin-skill-detail-trend-table-container">
          <Table
            rowKey="key"
            pagination={false}
            size="small"
            dataSource={trendRows}
            columns={[
              { title: "指标", dataIndex: "label", width: 80 },
              {
                title: `${statsWindow} 天趋势`,
                render: (_value: unknown, record: { label: string; points: Array<{ day: string; count: number }> }) =>
                  record.points.length ? (
                    <Space direction="vertical" size={8} style={{ width: "100%" }}>
                      {record.points.map((point) => (
                        <div key={`${record.label}-${point.day}`}>
                          <div style={{ display: "flex", justifyContent: "space-between", gap: 12 }}>
                            <Typography.Text>{point.day}</Typography.Text>
                            <Typography.Text>{point.count}</Typography.Text>
                          </div>
                          <Progress percent={Math.max(point.count, 0)} showInfo={false} strokeColor="#1677ff" />
                        </div>
                      ))}
                    </Space>
                  ) : (
                    <Typography.Text type="secondary">暂无数据</Typography.Text>
                  ),
              },
            ]}
          />
        </div>
      </Space>
    </Card>
  );
}
