import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Alert, Button, Card, DatePicker, Empty, Input, Select, Space, Table, Typography } from "antd";
import dayjs, { type Dayjs } from "dayjs";

import { API_BASE_URL, apiRequest } from "../lib/api";
import { hasPermission } from "../lib/permissions";
import { useAuthStore } from "../store/auth";

type AuditLogItem = {
  id: string;
  actor_display_name: string | null;
  action: string;
  target_type: string;
  target_id: string | null;
  request_id: string | null;
  before_json: Record<string, unknown> | null;
  after_json: Record<string, unknown> | null;
  created_at: string;
};

type PagedResponse<T> = {
  items: T[];
  total: number;
  page: number;
  page_size: number;
};

export function AuditLogsPage() {
  const accessToken = useAuthStore((state) => state.accessToken);
  const user = useAuthStore((state) => state.user);
  const [actor, setActor] = useState("");
  const [action, setAction] = useState<string | undefined>();
  const [targetType, setTargetType] = useState<string | undefined>();
  const [dateRange, setDateRange] = useState<[Dayjs | null, Dayjs | null] | null>(null);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);
  const canExport = hasPermission(user, "admin.audit.export");

  const queryString = new URLSearchParams();
  if (actor.trim()) {
    queryString.set("actor", actor.trim());
  }
  if (action) {
    queryString.set("action", action);
  }
  if (targetType) {
    queryString.set("target_type", targetType);
  }
  if (dateRange?.[0]) {
    queryString.set("date_from", dateRange[0].startOf("day").toISOString());
  }
  if (dateRange?.[1]) {
    queryString.set("date_to", dateRange[1].endOf("day").toISOString());
  }
  queryString.set("page", String(page));
  queryString.set("page_size", String(pageSize));

  const auditQuery = useQuery({
    queryKey: ["admin-audit-logs", accessToken, actor, action, targetType, dateRange?.[0]?.valueOf(), dateRange?.[1]?.valueOf(), page, pageSize],
    queryFn: () => apiRequest<PagedResponse<AuditLogItem>>(`/admin/audit-logs?${queryString.toString()}`, { token: accessToken }),
    placeholderData: (previous) => previous,
  });

  const exportMutation = useMutation({
    mutationFn: async () => {
      const exportQuery = new URLSearchParams(queryString);
      exportQuery.delete("page");
      exportQuery.delete("page_size");
      exportQuery.set("limit", "1000");
      const response = await fetch(`${API_BASE_URL}/admin/audit-logs/export?${exportQuery.toString()}`, {
        headers: accessToken ? { Authorization: `Bearer ${accessToken}` } : {},
      });
      if (!response.ok) {
        const payload = await response.json().catch(() => ({ detail: "导出失败" }));
        throw new Error(payload.detail ?? payload.message ?? "导出失败");
      }
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = "skill-hub-audit-logs.csv";
      anchor.click();
      URL.revokeObjectURL(url);
    },
  });

  return (
    <>
      <Card id="admin-audit-logs-filters-card" className="content-card filters-card">
        <Space wrap className="filters-row">
          <Input.Search
            value={actor}
            onChange={(event) => {
              setActor(event.target.value);
              setPage(1);
            }}
            allowClear
            placeholder="搜索操作人"
            className="filters-search"
          />
          <Select
            allowClear
            placeholder="全部动作"
            value={action}
            onChange={(value) => {
              setAction(value);
              setPage(1);
            }}
            className="filters-select"
            options={[
              { label: "skill.upload", value: "skill.upload" },
              { label: "version.submit", value: "version.submit" },
              { label: "version.approve", value: "version.approve" },
              { label: "version.reject", value: "version.reject" },
              { label: "version.publish", value: "version.publish" },
              { label: "version.rollback", value: "version.rollback" },
              { label: "category.update", value: "category.update" },
              { label: "user.roles.update", value: "user.roles.update" },
            ]}
          />
          <Select
            allowClear
            placeholder="全部目标"
            value={targetType}
            onChange={(value) => {
              setTargetType(value);
              setPage(1);
            }}
            className="filters-select"
            options={[
              { label: "skill_version", value: "skill_version" },
              { label: "category", value: "category" },
              { label: "user", value: "user" },
            ]}
          />
          <DatePicker.RangePicker
            value={dateRange}
            onChange={(value) => {
              setDateRange(value);
              setPage(1);
            }}
          />
          <Button onClick={() => exportMutation.mutate()} loading={exportMutation.isPending} disabled={!canExport}>
            导出 CSV
          </Button>
        </Space>
      </Card>

      <Card id="admin-audit-logs-table-card" className="content-card">
        {auditQuery.isError ? (
          <Alert type="error" showIcon message={(auditQuery.error as Error).message} />
        ) : auditQuery.data?.items.length ? (
          <div id="admin-audit-logs-table-container">
            <Table
              rowKey="id"
              pagination={{
                current: page,
                pageSize,
                total: auditQuery.data.total,
                showSizeChanger: true,
                onChange: (nextPage, nextPageSize) => {
                  setPage(nextPage);
                  setPageSize(nextPageSize);
                },
              }}
              dataSource={auditQuery.data.items}
              scroll={{ x: 1100 }}
              columns={[
                { title: "动作", dataIndex: "action" },
                { title: "操作人", dataIndex: "actor_display_name", render: (value: string | null) => value ?? "-" },
                { title: "目标", dataIndex: "target_type" },
                { title: "目标 ID", dataIndex: "target_id", render: (value: string | null) => value ?? "-" },
                { title: "请求 ID", dataIndex: "request_id", render: (value: string | null) => value ?? "-" },
                {
                  title: "快照",
                  render: (_: unknown, record: AuditLogItem) =>
                    record.before_json || record.after_json ? (
                      <Typography.Text code>{JSON.stringify({ before: record.before_json, after: record.after_json })}</Typography.Text>
                    ) : (
                      "-"
                    ),
                },
                { title: "时间", dataIndex: "created_at", render: (value: string) => dayjs(value).format("YYYY-MM-DD HH:mm:ss") },
              ]}
            />
          </div>
        ) : (
          <Empty description="暂无审计日志" />
        )}
      </Card>
      {!canExport ? <Typography.Text type="secondary">当前账号没有审计导出权限</Typography.Text> : null}
      {exportMutation.error ? <Alert style={{ marginTop: 16 }} type="error" showIcon message={(exportMutation.error as Error).message} /> : null}
    </>
  );
}
