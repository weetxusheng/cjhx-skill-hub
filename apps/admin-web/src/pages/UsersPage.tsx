import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Alert, Button, Card, Empty, Form, Input, Modal, Select, Space, Table, Tag, Typography } from "antd";
import dayjs from "dayjs";

import { apiRequest } from "../lib/api";
import { hasPermission } from "../lib/permissions";
import { useAuthStore } from "../store/auth";

type UserItem = {
  id: string;
  username: string;
  display_name: string;
  email: string | null;
  status: "active" | "disabled";
  roles: string[];
  last_login_at: string | null;
  created_at: string;
};

type RoleItem = {
  id: string;
  code: string;
  name: string;
  is_active: boolean;
};

type UserSkillGrantItem = {
  skill_id: string;
  skill_name: string;
  skill_slug: string;
  category_name: string;
  effective_scopes: string[];
  direct_scopes: string[];
  inherited_scopes: string[];
  inherited_roles: string[];
};

type PagedResponse<T> = {
  items: T[];
  total: number;
  page: number;
  page_size: number;
};

export function UsersPage() {
  const accessToken = useAuthStore((state) => state.accessToken);
  const user = useAuthStore((state) => state.user);
  const queryClient = useQueryClient();
  const [searchInput, setSearchInput] = useState("");
  const [statusFilter, setStatusFilter] = useState<string | undefined>();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [editingUser, setEditingUser] = useState<UserItem | null>(null);
  const [grantUser, setGrantUser] = useState<UserItem | null>(null);
  const [form] = Form.useForm<{ roles: string[] }>();
  const canManageUsers = hasPermission(user, "admin.users.manage");

  const usersQuery = useQuery({
    queryKey: ["admin-users", accessToken, searchInput, statusFilter, page, pageSize],
    queryFn: () => {
      const query = new URLSearchParams();
      if (searchInput.trim()) {
        query.set("q", searchInput.trim());
      }
      if (statusFilter) {
        query.set("status", statusFilter);
      }
      query.set("page", String(page));
      query.set("page_size", String(pageSize));
      return apiRequest<PagedResponse<UserItem>>(`/admin/users?${query.toString()}`, { token: accessToken });
    },
    placeholderData: (previous) => previous,
  });

  const rolesQuery = useQuery({
    queryKey: ["admin-role-options", accessToken],
    queryFn: () => apiRequest<RoleItem[]>("/admin/roles/options", { token: accessToken }),
  });

  const skillGrantsQuery = useQuery({
    queryKey: ["admin-user-skill-grants", accessToken, grantUser?.id],
    enabled: Boolean(accessToken && grantUser?.id),
    queryFn: () => apiRequest<UserSkillGrantItem[]>(`/admin/users/${grantUser?.id}/skill-grants`, { token: accessToken }),
  });

  const rolesMutation = useMutation({
    mutationFn: (roles: string[]) =>
      apiRequest<UserItem>(`/admin/users/${editingUser?.id}/roles`, {
        method: "POST",
        token: accessToken,
        body: JSON.stringify({ roles }),
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["admin-users"] });
      setEditingUser(null);
      form.resetFields();
    },
  });

  const statusMutation = useMutation({
    mutationFn: ({ userId, action }: { userId: string; action: "enable" | "disable" }) =>
      apiRequest<UserItem>(`/admin/users/${userId}/${action}`, {
        method: "POST",
        token: accessToken,
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["admin-users"] });
    },
  });

  const openRoleModal = (user: UserItem) => {
    setEditingUser(user);
    form.setFieldsValue({ roles: user.roles });
  };

  return (
    <>
      <Card id="admin-users-filters-card" className="content-card filters-card">
        <Space wrap className="filters-row">
          <Input.Search
            value={searchInput}
            onChange={(event) => {
              setSearchInput(event.target.value);
              setPage(1);
            }}
            allowClear
            placeholder="搜索用户名、显示名或邮箱"
            className="filters-search"
          />
          <Select
            allowClear
            placeholder="全部状态"
            value={statusFilter}
            onChange={(value) => {
              setStatusFilter(value);
              setPage(1);
            }}
            className="filters-select"
            options={[
              { label: "active", value: "active" },
              { label: "disabled", value: "disabled" },
            ]}
          />
        </Space>
      </Card>

      <Card id="admin-users-table-card" className="content-card">
        {usersQuery.isError ? (
          <Alert type="error" showIcon message={(usersQuery.error as Error).message} />
        ) : usersQuery.data?.items.length ? (
          <div id="admin-users-table-container">
            <Table
              rowKey="id"
              pagination={{
                current: page,
                pageSize,
                total: usersQuery.data.total,
                showSizeChanger: true,
                onChange: (nextPage, nextPageSize) => {
                  setPage(nextPage);
                  setPageSize(nextPageSize);
                },
              }}
              dataSource={usersQuery.data.items}
              columns={[
                { title: "用户名", dataIndex: "username" },
                { title: "显示名", dataIndex: "display_name" },
                { title: "邮箱", dataIndex: "email", render: (value: string | null) => value ?? "-" },
                { title: "角色", dataIndex: "roles", render: (value: string[]) => value.map((item) => <Tag key={item}>{item}</Tag>) },
                {
                  title: "状态",
                  dataIndex: "status",
                  render: (value: string) => <Tag color={value === "active" ? "green" : "default"}>{value}</Tag>,
                },
                {
                  title: "最近登录",
                  dataIndex: "last_login_at",
                  render: (value: string | null) => (value ? dayjs(value).format("YYYY-MM-DD HH:mm") : "-"),
                },
                {
                  title: "操作",
                  render: (_: unknown, record: UserItem) => (
                    <Space size={8}>
                      <Button size="small" onClick={() => setGrantUser(record)}>
                        查看 Skill 授权
                      </Button>
                      <Button size="small" onClick={() => openRoleModal(record)} disabled={!canManageUsers}>
                        配置角色
                      </Button>
                      {record.status === "active" ? (
                        <Button
                          size="small"
                          danger
                          onClick={() => statusMutation.mutate({ userId: record.id, action: "disable" })}
                          loading={statusMutation.isPending}
                          disabled={!canManageUsers}
                        >
                          禁用
                        </Button>
                      ) : (
                        <Button
                          size="small"
                          onClick={() => statusMutation.mutate({ userId: record.id, action: "enable" })}
                          loading={statusMutation.isPending}
                          disabled={!canManageUsers}
                        >
                          启用
                        </Button>
                      )}
                    </Space>
                  ),
                },
              ]}
            />
          </div>
        ) : (
          <Empty description="暂无用户数据" />
        )}
      </Card>

      <Modal
        wrapProps={{ id: "admin-users-skill-grants-modal" }}
        open={Boolean(grantUser)}
        title={grantUser ? `Skill 授权 · ${grantUser.display_name}` : "Skill 授权"}
        footer={null}
        width={860}
        onCancel={() => setGrantUser(null)}
        destroyOnClose
      >
        {skillGrantsQuery.isError ? (
          <Alert type="error" showIcon message={(skillGrantsQuery.error as Error).message} />
        ) : skillGrantsQuery.isPending ? (
          <div id="admin-users-skill-grants-table">
            <Table
              rowKey="skill_id"
              loading
              pagination={false}
              dataSource={[]}
              columns={[
                { title: "Skill", dataIndex: "skill_name" },
                { title: "分类", dataIndex: "category_name" },
                { title: "生效范围", dataIndex: "effective_scopes" },
              ]}
            />
          </div>
        ) : skillGrantsQuery.data?.length ? (
          <div id="admin-users-skill-grants-table">
            <Table
              rowKey="skill_id"
              pagination={false}
              dataSource={skillGrantsQuery.data}
              columns={[
                {
                  title: "Skill",
                  render: (_: unknown, record: UserSkillGrantItem) => (
                    <Space direction="vertical" size={0}>
                      <Typography.Text strong>{record.skill_name}</Typography.Text>
                      <Typography.Text type="secondary">{record.skill_slug}</Typography.Text>
                    </Space>
                  ),
                },
                { title: "分类", dataIndex: "category_name" },
                {
                  title: "生效范围",
                  dataIndex: "effective_scopes",
                  render: (value: string[]) => value.map((item) => <Tag color="blue" key={item}>{item}</Tag>),
                },
                {
                  title: "直接授权",
                  dataIndex: "direct_scopes",
                  render: (value: string[]) =>
                    value.length ? value.map((item) => <Tag color="gold" key={item}>{item}</Tag>) : <Typography.Text type="secondary">无</Typography.Text>,
                },
                {
                  title: "角色继承",
                  render: (_: unknown, record: UserSkillGrantItem) => (
                    <Space direction="vertical" size={4}>
                      {record.inherited_scopes.length ? (
                        <Space wrap>
                          {record.inherited_scopes.map((item) => (
                            <Tag color="green" key={item}>
                              {item}
                            </Tag>
                          ))}
                        </Space>
                      ) : (
                        <Typography.Text type="secondary">无</Typography.Text>
                      )}
                      {record.inherited_roles.length ? (
                        <Typography.Text type="secondary">{record.inherited_roles.join(" / ")}</Typography.Text>
                      ) : null}
                    </Space>
                  ),
                },
              ]}
            />
          </div>
        ) : (
          <Empty description="该用户当前没有 Skill 级授权" />
        )}
      </Modal>

      <Modal
        wrapProps={{ id: "admin-users-role-config-modal" }}
        open={Boolean(editingUser)}
        title={editingUser ? `配置角色 · ${editingUser.display_name}` : "配置角色"}
        okText="保存角色"
        confirmLoading={rolesMutation.isPending}
        onCancel={() => {
          setEditingUser(null);
          form.resetFields();
        }}
        onOk={() => form.submit()}
        destroyOnClose
      >
        <div id="admin-users-role-config-form">
          <Form form={form} layout="vertical" onFinish={(values) => rolesMutation.mutate(values.roles)}>
            <Form.Item label="角色" name="roles" rules={[{ required: true, message: "至少选择一个角色" }]}>
              <Select
                mode="multiple"
                options={(rolesQuery.data ?? [])
                  .filter((item) => item.is_active)
                  .map((item) => ({ label: `${item.name} (${item.code})`, value: item.code }))}
                disabled={!canManageUsers}
              />
            </Form.Item>
            {!canManageUsers ? <Typography.Text type="secondary">当前账号没有用户角色管理权限</Typography.Text> : null}
            {rolesMutation.error ? <Alert type="error" showIcon message={(rolesMutation.error as Error).message} /> : null}
          </Form>
        </div>
      </Modal>
    </>
  );
}
