import { useDeferredValue, useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Button, Card, Empty, Input, Pagination, Select, Space, Table, Tag, Typography } from "antd";
import dayjs from "dayjs";
import { Link, useNavigate } from "react-router-dom";

import { apiRequest } from "../lib/api";
import { useAuthStore } from "../store/auth";

type CategoryItem = {
  id: string;
  name: string;
  slug: string;
};

type AdminSkillListItem = {
  id: string;
  name: string;
  slug: string;
  status: string;
  category_name: string;
  category_slug: string;
  latest_version_no: string | null;
  latest_version_status: string | null;
  current_published_version: string | null;
  owner_display_name: string | null;
  pending_review_count: number;
  pending_release_count: number;
  like_count: number;
  favorite_count: number;
  download_count: number;
  current_published_version_id: string | null;
  published_at: string | null;
  created_at: string;
  updated_at: string;
};

type PagedResponse<T> = {
  items: T[];
  total: number;
  page: number;
  page_size: number;
};

export function SkillsPage() {
  const accessToken = useAuthStore((state) => state.accessToken);
  const navigate = useNavigate();
  const [searchInput, setSearchInput] = useState("");
  const [category, setCategory] = useState<string | undefined>();
  const [status, setStatus] = useState<string | undefined>();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const deferredSearch = useDeferredValue(searchInput.trim());

  useEffect(() => {
    setPage(1);
  }, [deferredSearch, category, status]);

  const categoriesQuery = useQuery({
    queryKey: ["admin-skill-categories", accessToken],
    queryFn: () => apiRequest<CategoryItem[]>("/admin/categories/options", { token: accessToken }),
  });

  const skillsQuery = useQuery({
    queryKey: ["admin-skill-list", accessToken, deferredSearch, category, status, page, pageSize],
    queryFn: () => {
      const query = new URLSearchParams({
        page: String(page),
        page_size: String(pageSize),
      });
      if (deferredSearch) {
        query.set("q", deferredSearch);
      }
      if (category) {
        query.set("category", category);
      }
      if (status) {
        query.set("status", status);
      }
      return apiRequest<PagedResponse<AdminSkillListItem>>(`/admin/skills?${query.toString()}`, { token: accessToken });
    },
  });

  const hasFilters = Boolean(deferredSearch || category || status);

  const columns = [
    {
      title: "技能",
      dataIndex: "name",
      key: "name",
      render: (_: string, record: AdminSkillListItem) => (
        <Space direction="vertical" size={0}>
          <Link to={`/skills/${record.id}`}>{record.name}</Link>
          <Typography.Text type="secondary">{record.slug}</Typography.Text>
        </Space>
      ),
    },
    { title: "分类", dataIndex: "category_name", key: "category_name" },
    {
      title: "负责人",
      dataIndex: "owner_display_name",
      key: "owner_display_name",
      render: (value: string | null) => value ?? "-",
    },
    {
      title: "主档状态",
      dataIndex: "status",
      key: "status",
      render: (value: string) => <Tag color={value === "active" ? "green" : "default"}>{value}</Tag>,
    },
    {
      title: "最新版本",
      key: "latest_version",
      render: (_: unknown, record: AdminSkillListItem) => (
        <Space direction="vertical" size={0}>
          <Typography.Text>{record.latest_version_no ?? "-"}</Typography.Text>
          <Tag>{record.latest_version_status ?? "unknown"}</Tag>
        </Space>
      ),
    },
    {
      title: "线上版本",
      dataIndex: "current_published_version",
      key: "current_published_version",
      render: (value: string | null) => (value ? <Tag color="green">v{value}</Tag> : <Tag>未发布</Tag>),
    },
    {
      title: "待办",
      key: "queues",
      render: (_: unknown, record: AdminSkillListItem) => (
        <Space wrap>
          <Tag color={record.pending_review_count ? "gold" : "default"}>待审核 {record.pending_review_count}</Tag>
          <Tag color={record.pending_release_count ? "blue" : "default"}>待发布 {record.pending_release_count}</Tag>
        </Space>
      ),
    },
    {
      title: "运营数据",
      key: "metrics",
      render: (_: unknown, record: AdminSkillListItem) => (
        <Space wrap>
          <Tag>赞 {record.like_count}</Tag>
          <Tag>收藏 {record.favorite_count}</Tag>
          <Tag>下载 {record.download_count}</Tag>
        </Space>
      ),
    },
    {
      title: "最近动作时间",
      dataIndex: "updated_at",
      key: "updated_at",
      render: (value: string) => dayjs(value).format("YYYY-MM-DD HH:mm"),
    },
  ];

  return (
    <>
      <Card id="admin-skills-filters-card" className="content-card filters-card">
        <Space size={[12, 12]} wrap className="filters-row">
          <Input.Search
            value={searchInput}
            onChange={(event) => setSearchInput(event.target.value)}
            placeholder="搜索技能名称、slug、摘要或分类"
            allowClear
            className="filters-search"
          />
          <Select
            allowClear
            placeholder="全部分类"
            value={category}
            onChange={(value) => setCategory(value)}
            className="filters-select"
            options={(categoriesQuery.data ?? []).map((item) => ({ label: item.name, value: item.slug }))}
          />
          <Select
            allowClear
            placeholder="全部状态"
            value={status}
            onChange={(value) => setStatus(value)}
            className="filters-select"
            options={[
              { label: "active", value: "active" },
              { label: "inactive", value: "inactive" },
            ]}
          />
          <Button
            onClick={() => {
              setSearchInput("");
              setCategory(undefined);
              setStatus(undefined);
              setPage(1);
            }}
          >
            清空筛选
          </Button>
        </Space>
      </Card>

      <Card id="admin-skills-table-card" className="content-card" title={`技能主档 (${skillsQuery.data?.total ?? 0})`}>
        {skillsQuery.isError ? (
          <Typography.Text type="danger">{(skillsQuery.error as Error).message}</Typography.Text>
        ) : skillsQuery.data?.items.length ? (
          <>
            <div id="admin-skills-table-container">
              <Table rowKey="id" pagination={false} columns={columns} dataSource={skillsQuery.data.items} />
            </div>
            <div id="admin-skills-pagination-row" className="pagination-row">
              <Pagination
                current={page}
                pageSize={pageSize}
                total={skillsQuery.data.total}
                showSizeChanger
                onChange={(nextPage, nextPageSize) => {
                  setPage(nextPage);
                  setPageSize(nextPageSize);
                }}
              />
            </div>
          </>
        ) : (
          <Empty description={hasFilters ? "没有匹配当前筛选条件的技能" : "当前还没有技能主档数据"} />
        )}
      </Card>
    </>
  );
}
