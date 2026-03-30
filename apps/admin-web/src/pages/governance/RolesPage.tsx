import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Alert, Button, Card, Checkbox, Empty, Form, Input, Modal, Popconfirm, Select, Space, Table, Tag, Typography, message } from "antd";

import { AdminFiltersRefreshButton, AdminKeywordSearchCompact } from "../../components/AdminListToolbar";
import { apiRequest } from "../../lib/api";
import { hasPermission } from "../../lib/permissions";
import { useAuthStore } from "../../store/auth";

type RoleItem = {
  id: string;
  code: string;
  name: string;
  description: string | null;
  is_system: boolean;
  is_active: boolean;
  permission_codes: string[];
  created_at: string;
};

type PermissionItem = {
  code: string;
  name: string;
  description: string | null;
  group_key: string;
};

type RoleFormValue = {
  code: string;
  name: string;
  description: string;
  permission_codes: string[];
};

type PagedResponse<T> = {
  items: T[];
  total: number;
  page: number;
  page_size: number;
};

/**
 * 治理 - 角色与权限矩阵
 *
 * 交互约定：
 * - 加载态：角色分页列表与权限字典加载分离；模态内表单在打开后填充。
 * - 空态：无自定义角色时表格可能为空；权限分组由接口返回决定。
 * - 错误态：请求失败时在页面展示错误文案。
 * - 权限不足态：无 `admin.roles.manage` 时不可创建/编辑/停用/删除角色，系统角色通常不可删。
 * - 筛选：关键字与启用状态走服务端分页；变更筛选时重置页码。
 *
 * 变更成功后会失效 `admin-roles` 等相关 query，保证列表与下拉选项一致。
 */
export function RolesPage() {
  const accessToken = useAuthStore((state) => state.accessToken);
  const user = useAuthStore((state) => state.user);
  const queryClient = useQueryClient();
  const [form] = Form.useForm<RoleFormValue>();
  const [modalOpen, setModalOpen] = useState(false);
  const [editingRole, setEditingRole] = useState<RoleItem | null>(null);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [searchDraft, setSearchDraft] = useState("");
  const [searchApplied, setSearchApplied] = useState("");
  const [activeFilter, setActiveFilter] = useState<boolean | undefined>();
  const canManageRoles = hasPermission(user, "admin.roles.manage");

  const rolesQuery = useQuery({
    queryKey: ["admin-roles", accessToken, page, pageSize, searchApplied, activeFilter],
    queryFn: () => {
      const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
      if (searchApplied) {
        params.set("q", searchApplied);
      }
      if (activeFilter !== undefined) {
        params.set("is_active", String(activeFilter));
      }
      return apiRequest<PagedResponse<RoleItem>>(`/admin/roles?${params.toString()}`, { token: accessToken });
    },
    placeholderData: (previous) => previous,
  });

  const permissionsQuery = useQuery({
    queryKey: ["admin-permissions", accessToken],
    queryFn: () => apiRequest<PermissionItem[]>("/admin/permissions", { token: accessToken }),
  });

  const saveMutation = useMutation({
    mutationFn: async (values: RoleFormValue) => {
      const payload = { code: values.code, name: values.name, description: values.description || null };
      const role = editingRole
        ? await apiRequest<RoleItem>(`/admin/roles/${editingRole.id}`, {
            method: "PATCH",
            token: accessToken,
            body: JSON.stringify(payload),
          })
        : await apiRequest<RoleItem>("/admin/roles", {
            method: "POST",
            token: accessToken,
            body: JSON.stringify(payload),
          });
      return apiRequest<RoleItem>(`/admin/roles/${role.id}/permissions`, {
        method: "POST",
        token: accessToken,
        body: JSON.stringify({ permission_codes: values.permission_codes }),
      });
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["admin-roles"] });
      message.success(editingRole ? "角色已保存。" : "角色已创建。");
      setModalOpen(false);
      setEditingRole(null);
      form.resetFields();
    },
    onError: (error: Error) => {
      message.error(error.message);
    },
  });

  const statusMutation = useMutation({
    mutationFn: ({ roleId, action }: { roleId: string; action: "enable" | "disable" }) =>
      apiRequest<RoleItem>(`/admin/roles/${roleId}/${action}`, { method: "POST", token: accessToken }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["admin-roles"] });
      message.success("角色状态已更新。");
    },
    onError: (error: Error) => {
      message.error(error.message);
    },
  });

  const groupedPermissions = (permissionsQuery.data ?? []).reduce<Record<string, PermissionItem[]>>((acc, item) => {
    acc[item.group_key] = acc[item.group_key] ?? [];
    acc[item.group_key].push(item);
    return acc;
  }, {});

  const toKebab = (value: string) =>
    value
      .trim()
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "");

  const openCreate = () => {
    setEditingRole(null);
    form.setFieldsValue({ code: "", name: "", description: "", permission_codes: [] });
    setModalOpen(true);
  };

  const openEdit = (role: RoleItem) => {
    setEditingRole(role);
    form.setFieldsValue({
      code: role.code,
      name: role.name,
      description: role.description ?? "",
      permission_codes: role.permission_codes,
    });
    setModalOpen(true);
  };

  const runKeywordSearch = () => {
    setSearchApplied(searchDraft.trim());
    setPage(1);
  };

  const handleRefreshFilters = () => {
    setSearchDraft("");
    setSearchApplied("");
    setActiveFilter(undefined);
    setPage(1);
    void queryClient.invalidateQueries({ queryKey: ["admin-roles"] });
  };

  return (
    <>
      <Card id="admin-roles-filters-card" className="content-card filters-card">
        <div className="admin-list-toolbar">
          <div className="admin-list-toolbar__filters">
            <AdminKeywordSearchCompact
              value={searchDraft}
              onChange={setSearchDraft}
              onSearch={runKeywordSearch}
              placeholder="搜索角色 code、名称或描述"
            />
            <Select
              allowClear
              className="filters-select"
              placeholder="全部状态"
              value={activeFilter}
              onChange={(value) => {
                setActiveFilter(value as boolean | undefined);
                setPage(1);
              }}
              options={[
                { label: "启用", value: true },
                { label: "停用", value: false },
              ]}
            />
            <AdminFiltersRefreshButton onClick={handleRefreshFilters} />
          </div>
          <div className="admin-list-toolbar__actions">
            <Button type="primary" onClick={openCreate} disabled={!canManageRoles}>
              新建角色
            </Button>
            {!canManageRoles ? <Typography.Text type="secondary">当前账号没有角色管理权限</Typography.Text> : null}
          </div>
        </div>
      </Card>

      <Card id="admin-roles-table-card" className="content-card">
        {rolesQuery.isError ? (
          <Alert type="error" showIcon message={(rolesQuery.error as Error).message} />
        ) : rolesQuery.data?.items.length ? (
          <div id="admin-roles-table-container">
            <Table
              rowKey="id"
              pagination={{
                current: page,
                pageSize,
                total: rolesQuery.data.total,
                showSizeChanger: true,
                onChange: (nextPage, nextPageSize) => {
                  setPage(nextPage);
                  setPageSize(nextPageSize);
                },
              }}
              dataSource={rolesQuery.data.items}
              columns={[
                {
                  title: "角色",
                  render: (_: unknown, record: RoleItem) => (
                    <Space direction="vertical" size={0}>
                      <Typography.Text strong>{record.name}</Typography.Text>
                      <Typography.Text type="secondary">{record.code}</Typography.Text>
                    </Space>
                  ),
                },
                {
                  title: "状态",
                  render: (_: unknown, record: RoleItem) => (
                    <Space wrap>
                      <Tag color={record.is_active ? "green" : "default"}>{record.is_active ? "启用" : "停用"}</Tag>
                      {record.is_system ? <Tag color="blue">系统角色</Tag> : null}
                    </Space>
                  ),
                },
                { title: "描述", dataIndex: "description", render: (value: string | null) => value ?? "-" },
                {
                  title: "权限点",
                  dataIndex: "permission_codes",
                  render: (value: string[]) => <Typography.Text>{value.length ? `${value.length} 个权限` : "未配置权限"}</Typography.Text>,
                },
                {
                  title: "操作",
                  render: (_: unknown, record: RoleItem) => (
                    <Space size={8}>
                      <Button size="small" onClick={() => openEdit(record)} disabled={!canManageRoles}>
                        编辑
                      </Button>
                      {record.is_active ? (
                        <Popconfirm
                          title="停用角色"
                          description="停用后，该角色将不再授予用户任何后台权限。"
                          okButtonProps={{ loading: statusMutation.isPending }}
                          onConfirm={() => statusMutation.mutate({ roleId: record.id, action: "disable" })}
                        >
                          <Button size="small" danger disabled={!canManageRoles}>
                            停用
                          </Button>
                        </Popconfirm>
                      ) : (
                        <Popconfirm
                          title="启用角色"
                          description="启用后，绑定该角色的用户会重新获得这组后台权限。"
                          okButtonProps={{ loading: statusMutation.isPending }}
                          onConfirm={() => statusMutation.mutate({ roleId: record.id, action: "enable" })}
                        >
                          <Button size="small" disabled={!canManageRoles}>
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
          <Empty description="暂无角色数据" />
        )}
      </Card>

      <Modal
        wrapProps={{ id: "admin-roles-editor-modal" }}
        open={modalOpen}
        title={editingRole ? `编辑角色 · ${editingRole.name}` : "新建角色"}
        okText={editingRole ? "保存角色" : "创建角色"}
        confirmLoading={saveMutation.isPending}
        onCancel={() => {
          setModalOpen(false);
          setEditingRole(null);
          form.resetFields();
        }}
        onOk={() => form.submit()}
        width={760}
        destroyOnClose
      >
        <div id="admin-roles-editor-form">
          <Form form={form} layout="vertical" onFinish={(values) => saveMutation.mutate(values)}>
            <Form.Item label="角色名称" name="name" rules={[{ required: true, message: "请输入角色名称" }]}>
              <Input disabled={!canManageRoles} />
            </Form.Item>
            <Form.Item label="角色编码" name="code" rules={[{ required: true, message: "请输入角色编码" }]}>
              <Input disabled={!canManageRoles || Boolean(editingRole?.is_system)} />
            </Form.Item>
            <Form.Item label="描述" name="description">
              <Input.TextArea rows={3} disabled={!canManageRoles} />
            </Form.Item>
            <Form.Item label="权限点" name="permission_codes" rules={[{ required: true, message: "请至少选择一个权限点" }]}>
              <Checkbox.Group style={{ width: "100%" }} disabled={!canManageRoles}>
                <Space direction="vertical" size={16} style={{ width: "100%" }}>
                  {Object.entries(groupedPermissions).map(([groupKey, items]) => (
                    <Card key={groupKey} id={`admin-roles-permission-group-${toKebab(groupKey)}`} size="small" title={groupKey === "skill" ? "Skill 权限" : "后台治理权限"}>
                      <Space direction="vertical" size={12} style={{ width: "100%" }}>
                        {items.map((item) => (
                          <Checkbox key={item.code} value={item.code}>
                            <Space direction="vertical" size={0}>
                              <Typography.Text>{item.name}</Typography.Text>
                              <Typography.Text type="secondary">{item.code}</Typography.Text>
                            </Space>
                          </Checkbox>
                        ))}
                      </Space>
                    </Card>
                  ))}
                </Space>
              </Checkbox.Group>
            </Form.Item>
            {saveMutation.error ? <Alert type="error" showIcon message={(saveMutation.error as Error).message} /> : null}
          </Form>
        </div>
      </Modal>
    </>
  );
}
