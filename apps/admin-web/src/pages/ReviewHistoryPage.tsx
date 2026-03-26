import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Alert, Card, Input, Select, Space, Table, Tag, Typography } from "antd";
import dayjs from "dayjs";
import { Link } from "react-router-dom";

import { apiRequest } from "../lib/api";
import { useAuthStore } from "../store/auth";

type ReviewHistoryItem = {
  version_id: string;
  skill_id: string;
  skill_name: string;
  version: string;
  category_name: string;
  action: "approve" | "reject" | "publish" | "archive" | "rollback_publish";
  comment: string;
  operator_display_name: string;
  created_at: string;
};

const ACTION_LABELS: Record<ReviewHistoryItem["action"], string> = {
  approve: "审核通过",
  reject: "审核拒绝",
  publish: "正式发布",
  archive: "归档下线",
  rollback_publish: "回滚发布",
};

export function ReviewHistoryPage() {
  const accessToken = useAuthStore((state) => state.accessToken);
  const [actionFilter, setActionFilter] = useState<string | undefined>();
  const [keyword, setKeyword] = useState("");

  const historyQuery = useQuery({
    queryKey: ["admin-review-history", accessToken],
    queryFn: () => apiRequest<ReviewHistoryItem[]>("/admin/reviews/history", { token: accessToken }),
  });

  const filteredItems = useMemo(() => {
    const search = keyword.trim().toLowerCase();
    return (historyQuery.data ?? []).filter((item) => {
      if (actionFilter && item.action !== actionFilter) {
        return false;
      }
      if (!search) {
        return true;
      }
      return [item.skill_name, item.category_name, item.operator_display_name, item.comment, item.version]
        .filter(Boolean)
        .some((value) => value.toLowerCase().includes(search));
    });
  }, [actionFilter, historyQuery.data, keyword]);

  return (
    <>
      <Card id="admin-review-history-filters-card" className="content-card filters-card">
        <Space wrap className="filters-row">
          <Input.Search
            allowClear
            className="filters-search"
            placeholder="搜索技能、分类、操作人或说明"
            value={keyword}
            onChange={(event) => setKeyword(event.target.value)}
          />
          <Select
            allowClear
            className="filters-select"
            placeholder="全部动作"
            value={actionFilter}
            onChange={setActionFilter}
            options={Object.entries(ACTION_LABELS).map(([value, label]) => ({ value, label }))}
          />
          <Tag color="processing">已处理 {filteredItems.length}</Tag>
        </Space>
      </Card>

      <Card id="admin-review-history-table-card" className="content-card">
        {historyQuery.isError ? (
          <Alert type="error" showIcon message={(historyQuery.error as Error).message} />
        ) : (
          <div id="admin-review-history-table-container">
            <Table
              rowKey={(record) => `${record.version_id}-${record.action}-${record.created_at}`}
              pagination={{ pageSize: 12 }}
              dataSource={filteredItems}
              columns={[
                {
                  title: "技能 / 版本",
                  render: (_: unknown, record: ReviewHistoryItem) => (
                    <Space direction="vertical" size={0}>
                      <Link to={`/versions/${record.version_id}`}>{record.skill_name}</Link>
                      <Typography.Text type="secondary">v{record.version}</Typography.Text>
                    </Space>
                  ),
                },
                { title: "分类", dataIndex: "category_name" },
                {
                  title: "动作",
                  dataIndex: "action",
                  render: (value: ReviewHistoryItem["action"]) => <Tag>{ACTION_LABELS[value]}</Tag>,
                },
                { title: "操作人", dataIndex: "operator_display_name" },
                {
                  title: "说明",
                  dataIndex: "comment",
                  render: (value: string) => value || "-",
                },
                {
                  title: "时间",
                  dataIndex: "created_at",
                  render: (value: string) => dayjs(value).format("YYYY-MM-DD HH:mm"),
                },
              ]}
            />
          </div>
        )}
      </Card>
    </>
  );
}
