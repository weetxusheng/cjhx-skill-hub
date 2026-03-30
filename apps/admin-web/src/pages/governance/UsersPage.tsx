import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { QuestionCircleOutlined } from "@ant-design/icons";
import { Alert, Button, Card, Empty, Form, Modal, Popconfirm, Select, Space, Table, Tag, Tooltip, Typography, message } from "antd";
import dayjs from "dayjs";

import { AdminFiltersRefreshButton, AdminKeywordSearchCompact } from "../../components/AdminListToolbar";
import { apiRequest } from "../../lib/api";
import { hasPermission } from "../../lib/permissions";
import { formatSkillScopeLabel } from "../../lib/skillScopeLabels";
import { useAuthStore } from "../../store/auth";

type DepartmentBrief = {
  id: string;
  name: string;
};

type UserItem = {
  id: string;
  username: string;
  display_name: string;
  email: string | null;
  primary_department?: DepartmentBrief | null;
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

function SkillGrantColumnTitle({ label, tip }: { label: string; tip: string }) {
  return (
    <Space size={4}>
      <span>{label}</span>
      <Tooltip title={tip}>
        <QuestionCircleOutlined style={{ color: "var(--ant-color-text-tertiary, rgba(0,0,0,0.45))", cursor: "help" }} />
      </Tooltip>
    </Space>
  );
}

const SKILL_GRANT_MODAL_INTRO =
  "下表按「技能」汇总：生效范围 = 直接授权与角色继承的合并结果；直接授权是只给本人的；角色继承是因担任某角色而自动带上的。";

/**
 * 治理 - 用户与角色绑定、技能授权查看
 *
 * 交互约定：
 * - 加载态：用户列表与弹窗内子查询各自独立；打开弹窗时可能出现内层加载。
 * - 空态：无用户时表格为空；授权明细弹窗内无数据时由子表格 Empty 处理。
 * - 错误态：列表或变更失败时在对应区域展示错误信息。
 * - 权限不足态：无 `admin.users.manage` 时不可编辑角色或发起授权相关写操作，仅只读或提示。
 *
 * 分页与搜索：服务端分页；搜索/状态筛选变化时配合 `page` 重置（与实现一致）。
 */
export function UsersPage() {
  const accessToken = useAuthStore((state) => state.accessToken);
  const user = useAuthStore((state) => state.user);
  const queryClient = useQueryClient();
  const [searchDraft, setSearchDraft] = useState("");
  const [searchApplied, setSearchApplied] = useState("");
  const [statusFilter, setStatusFilter] = useState<string | undefined>();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [editingUser, setEditingUser] = useState<UserItem | null>(null);
  const [grantUser, setGrantUser] = useState<UserItem | null>(null);
  const [form] = Form.useForm<{ roles: string[] }>();
  const canManageUsers = hasPermission(user, "admin.users.manage");

  const usersQuery = useQuery({
    queryKey: ["admin-users", accessToken, searchApplied, statusFilter, page, pageSize],
    queryFn: () => {
      const query = new URLSearchParams();
      if (searchApplied) {
        query.set("q", searchApplied);
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

  const roleNameByCode = useMemo(() => {
    const map = new Map<string, string>();
    for (const r of rolesQuery.data ?? []) {
      map.set(r.code, r.name);
    }
    return map;
  }, [rolesQuery.data]);

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
      message.success("用户角色已更新。");
      setEditingUser(null);
      form.resetFields();
    },
    onError: (error: Error) => {
      message.error(error.message);
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
      message.success("用户状态已更新。");
    },
    onError: (error: Error) => {
      message.error(error.message);
    },
  });

  const openRoleModal = (user: UserItem) => {
    setEditingUser(user);
    form.setFieldsValue({ roles: user.roles });
  };

  const runKeywordSearch = () => {
    setSearchApplied(searchDraft.trim());
    setPage(1);
  };

  const handleRefreshFilters = () => {
    setSearchDraft("");
    setSearchApplied("");
    setStatusFilter(undefined);
    setPage(1);
    void queryClient.invalidateQueries({ queryKey: ["admin-users"] });
  };

  return (
    <>
      <Card id="admin-users-filters-card" className="content-card filters-card">
        <div className="admin-list-toolbar">
          <div className="admin-list-toolbar__filters">
            <AdminKeywordSearchCompact
              value={searchDraft}
              onChange={setSearchDraft}
              onSearch={runKeywordSearch}
              placeholder="搜索用户名、显示名、邮箱或一级部门"
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
                { label: "正常", value: "active" },
                { label: "已禁用", value: "disabled" },
              ]}
            />
            <AdminFiltersRefreshButton onClick={handleRefreshFilters} />
          </div>
        </div>
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
                {
                  title: "一级部门",
                  dataIndex: "primary_department",
                  render: (value: DepartmentBrief | null | undefined) => value?.name ?? "—",
                },
                { title: "邮箱", dataIndex: "email", render: (value: string | null) => value ?? "-" },
                {
                  title: "角色",
                  dataIndex: "roles",
                  render: (value: string[]) =>
                    value.map((code) => (
                      <Tag key={code}>{roleNameByCode.get(code) ?? code}</Tag>
                    )),
                },
                {
                  title: "状态",
                  dataIndex: "status",
                  render: (value: string) => (
                    <Tag color={value === "active" ? "green" : "default"}>{value === "active" ? "正常" : "已禁用"}</Tag>
                  ),
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
                        查看技能授权
                      </Button>
                      <Button size="small" onClick={() => openRoleModal(record)} disabled={!canManageUsers}>
                        配置角色
                      </Button>
                      {record.status === "active" ? (
                        <Popconfirm
                          title="禁用用户"
                          description="禁用后，该用户的后台访问与刷新会话会立即失效。"
                          okButtonProps={{ loading: statusMutation.isPending }}
                          onConfirm={() => statusMutation.mutate({ userId: record.id, action: "disable" })}
                        >
                          <Button
                            size="small"
                            danger
                            loading={statusMutation.isPending}
                            disabled={!canManageUsers}
                          >
                            禁用
                          </Button>
                        </Popconfirm>
                      ) : (
                        <Popconfirm
                          title="启用用户"
                          description="启用后，该用户可重新登录并继续访问被授权的功能。"
                          okButtonProps={{ loading: statusMutation.isPending }}
                          onConfirm={() => statusMutation.mutate({ userId: record.id, action: "enable" })}
                        >
                          <Button
                            size="small"
                            loading={statusMutation.isPending}
                            disabled={!canManageUsers}
                          >
                            启用
                          </Button>
                        </Popconfirm>
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
        title={grantUser ? `技能授权 · ${grantUser.display_name}` : "技能授权"}
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
                { title: "技能", dataIndex: "skill_name" },
                { title: "分类", dataIndex: "category_name" },
                { title: "生效范围", dataIndex: "effective_scopes" },
              ]}
            />
          </div>
        ) : skillGrantsQuery.data?.length ? (
          <div id="admin-users-skill-grants-table">
            <Typography.Paragraph type="secondary" style={{ marginBottom: 16 }}>
              {SKILL_GRANT_MODAL_INTRO}
            </Typography.Paragraph>
            <Table
              rowKey="skill_id"
              pagination={false}
              dataSource={skillGrantsQuery.data}
              columns={[
                {
                  title: "技能",
                  render: (_: unknown, record: UserSkillGrantItem) => (
                    <Space direction="vertical" size={0}>
                      <Typography.Text strong>{record.skill_name}</Typography.Text>
                      <Typography.Text type="secondary">{record.skill_slug}</Typography.Text>
                    </Space>
                  ),
                },
                { title: "分类", dataIndex: "category_name" },
                {
                  title: (
                    <SkillGrantColumnTitle
                      label="生效范围"
                      tip="在该技能上，该用户最终可用的权限范围（「直接授权」与「角色继承」合并、去重后的结果）。看这一列即可判断其在本技能上能执行哪些操作。"
                    />
                  ),
                  dataIndex: "effective_scopes",
                  render: (value: string[]) =>
                    value.map((item) => (
                      <Tag color="blue" key={item}>
                        {formatSkillScopeLabel(item)}
                      </Tag>
                    )),
                },
                {
                  title: (
                    <SkillGrantColumnTitle
                      label="直接授权"
                      tip="管理员在技能上「点名授予该用户」的范围，记录在用户直授表中，与是否担任全局角色无关。仅本人被单独加授权时才有内容。"
                    />
                  ),
                  dataIndex: "direct_scopes",
                  render: (value: string[]) =>
                    value.length ? (
                      value.map((item) => (
                        <Tag color="gold" key={item}>
                          {formatSkillScopeLabel(item)}
                        </Tag>
                      ))
                    ) : (
                      <Typography.Text type="secondary">无</Typography.Text>
                    ),
                },
                {
                  title: (
                    <SkillGrantColumnTitle
                      label="角色继承"
                      tip="因用户担任的某个全局角色，在该技能上被配置了 skill 级授权，从而间接获得的范围。下方小字为贡献来源的角色名称（中文名）。"
                    />
                  ),
                  render: (_: unknown, record: UserSkillGrantItem) => (
                    <Space direction="vertical" size={4}>
                      {record.inherited_scopes.length ? (
                        <Space wrap>
                          {record.inherited_scopes.map((item) => (
                            <Tag color="green" key={item}>
                              {formatSkillScopeLabel(item)}
                            </Tag>
                          ))}
                        </Space>
                      ) : (
                        <Typography.Text type="secondary">无</Typography.Text>
                      )}
                      {record.inherited_roles.length ? (
                        <Typography.Text type="secondary">{record.inherited_roles.join("、")}</Typography.Text>
                      ) : null}
                    </Space>
                  ),
                },
              ]}
            />
          </div>
        ) : (
          <Empty description="该用户当前没有技能级授权" />
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
                  .map((item) => ({ label: item.name, value: item.code }))}
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
