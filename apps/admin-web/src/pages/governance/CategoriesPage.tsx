import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Alert, Button, Card, Empty, Form, Input, InputNumber, Modal, Popconfirm, Space, Switch, Table, Tag, message } from "antd";

import { apiRequest } from "../../lib/api";
import { hasPermission } from "../../lib/permissions";
import { useAuthStore } from "../../store/auth";
import { CategoriesFiltersCard } from "./_components/CategoriesFiltersCard";

type CategoryItem = {
  id: string;
  name: string;
  slug: string;
  icon: string | null;
  description: string | null;
  sort_order: number;
  is_visible: boolean;
  skill_count: number;
};

type CategoryFormValue = {
  name: string;
  slug: string;
  icon: string | null;
  description: string | null;
  sort_order: number;
  is_visible: boolean;
};

/**
 * 治理 - 分类管理
 *
 * 交互约定：
 * - 加载态：表格依赖 `categoriesQuery`；首次加载可能显示骨架或空白直至数据返回。
 * - 空态：无分类时表格为空。
 * - 错误态：在页面内以 Alert 或文案展示（与现有实现一致）。
 * - 权限不足态：无 `admin.categories.manage` 时仅展示只读提示与列表，不提供新建/编辑/删除入口。
 *
 * 变更后通过 `invalidateQueries(["admin-categories"])` 刷新列表；分类选项亦被技能列表等复用。
 */
export function CategoriesPage() {
  const accessToken = useAuthStore((state) => state.accessToken);
  const user = useAuthStore((state) => state.user);
  const queryClient = useQueryClient();
  const [form] = Form.useForm<CategoryFormValue>();
  const [modalOpen, setModalOpen] = useState(false);
  const [editingCategory, setEditingCategory] = useState<CategoryItem | null>(null);
  const [keywordDraft, setKeywordDraft] = useState("");
  const [keywordApplied, setKeywordApplied] = useState("");
  const [visibleFilter, setVisibleFilter] = useState<boolean | undefined>();
  const canManage = hasPermission(user, "admin.categories.manage");

  const categoriesQuery = useQuery({
    queryKey: ["admin-categories", accessToken],
    queryFn: () => apiRequest<CategoryItem[]>("/admin/categories", { token: accessToken }),
  });

  const upsertMutation = useMutation({
    mutationFn: async (values: CategoryFormValue) => {
      const path = editingCategory ? `/admin/categories/${editingCategory.id}` : "/admin/categories";
      const method = editingCategory ? "PATCH" : "POST";
      return apiRequest<CategoryItem>(path, { method, token: accessToken, body: JSON.stringify(values) });
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["admin-categories"] });
      message.success(editingCategory ? "分类已保存。" : "分类已创建。");
      setEditingCategory(null);
      setModalOpen(false);
      form.resetFields();
    },
    onError: (error: Error) => {
      message.error(error.message);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (categoryId: string) => apiRequest(`/admin/categories/${categoryId}`, { method: "DELETE", token: accessToken }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["admin-categories"] });
      message.success("分类已删除。");
    },
    onError: (error: Error) => {
      message.error(error.message);
    },
  });

  const openCreate = () => {
    setEditingCategory(null);
    form.setFieldsValue({ name: "", slug: "", icon: null, description: null, sort_order: 0, is_visible: true });
    setModalOpen(true);
  };

  const filteredCategories = useMemo(() => {
    let list = categoriesQuery.data ?? [];
    if (visibleFilter !== undefined) {
      list = list.filter((c) => c.is_visible === visibleFilter);
    }
    const s = keywordApplied.toLowerCase();
    if (s) {
      list = list.filter((c) =>
        [c.name, c.slug, c.description ?? "", c.icon ?? ""].some((f) => f.toLowerCase().includes(s)),
      );
    }
    return list;
  }, [categoriesQuery.data, visibleFilter, keywordApplied]);

  const openEdit = (category: CategoryItem) => {
    setEditingCategory(category);
    form.setFieldsValue({
      name: category.name,
      slug: category.slug,
      icon: category.icon,
      description: category.description,
      sort_order: category.sort_order,
      is_visible: category.is_visible,
    });
    setModalOpen(true);
  };

  const runKeywordSearch = () => {
    setKeywordApplied(keywordDraft.trim());
  };

  const handleRefreshFilters = () => {
    setKeywordDraft("");
    setKeywordApplied("");
    setVisibleFilter(undefined);
    void queryClient.invalidateQueries({ queryKey: ["admin-categories"] });
  };

  return (
    <>
      <CategoriesFiltersCard
        keywordDraft={keywordDraft}
        onKeywordDraftChange={setKeywordDraft}
        onKeywordSearch={runKeywordSearch}
        visibleFilter={visibleFilter}
        onVisibleFilterChange={setVisibleFilter}
        onRefreshFilters={handleRefreshFilters}
        onOpenCreate={openCreate}
        canManage={canManage}
      />

      <Card id="admin-categories-table-card" className="content-card">
        {categoriesQuery.isError ? (
          <Alert type="error" showIcon message={(categoriesQuery.error as Error).message} />
        ) : categoriesQuery.data?.length ? (
          <div id="admin-categories-table-container">
            {filteredCategories.length ? (
            <Table
              rowKey="id"
              pagination={false}
              dataSource={filteredCategories}
              columns={[
                { title: "分类", dataIndex: "name" },
                { title: "Slug", dataIndex: "slug" },
                { title: "技能数", dataIndex: "skill_count" },
                { title: "排序", dataIndex: "sort_order" },
                {
                  title: "展示",
                  dataIndex: "is_visible",
                  render: (value: boolean) => <Tag color={value ? "green" : "default"}>{value ? "显示" : "隐藏"}</Tag>,
                },
                { title: "说明", dataIndex: "description", render: (value: string | null) => value ?? "-" },
                {
                  title: "操作",
                  render: (_: unknown, record: CategoryItem) => (
                    <Space size={8}>
                      <Button size="small" onClick={() => openEdit(record)} disabled={!canManage}>
                        编辑
                      </Button>
                      <Popconfirm
                        title="删除分类"
                        description="删除前会校验是否仍有技能在使用该分类。"
                        onConfirm={() => deleteMutation.mutate(record.id)}
                        okButtonProps={{ loading: deleteMutation.isPending }}
                      >
                        <Button size="small" danger disabled={!canManage}>
                          删除
                        </Button>
                      </Popconfirm>
                    </Space>
                  ),
                },
              ]}
            />
            ) : (
              <Empty description="没有匹配当前筛选的分类" />
            )}
          </div>
        ) : (
          <Empty description="暂无分类数据" />
        )}
      </Card>

      <Modal
        wrapProps={{ id: "admin-categories-editor-modal" }}
        open={modalOpen}
        title={editingCategory ? "编辑分类" : "新建分类"}
        okText={editingCategory ? "保存" : "创建"}
        confirmLoading={upsertMutation.isPending}
        onCancel={() => {
          setEditingCategory(null);
          setModalOpen(false);
          form.resetFields();
        }}
        onOk={() => form.submit()}
        destroyOnClose
      >
        <div id="admin-categories-editor-form">
          <Form form={form} layout="vertical" onFinish={(values) => upsertMutation.mutate(values)}>
            <Form.Item label="名称" name="name" rules={[{ required: true, message: "请输入分类名称" }]}>
              <Input />
            </Form.Item>
            <Form.Item label="Slug" name="slug" rules={[{ required: true, message: "请输入分类 slug" }]}>
              <Input />
            </Form.Item>
            <Form.Item label="图标" name="icon">
              <Input />
            </Form.Item>
            <Form.Item label="说明" name="description">
              <Input.TextArea rows={3} />
            </Form.Item>
            <Form.Item label="排序" name="sort_order">
              <InputNumber min={0} max={9999} style={{ width: "100%" }} />
            </Form.Item>
            <Form.Item label="前台显示" name="is_visible" valuePropName="checked">
              <Switch />
            </Form.Item>
            {upsertMutation.error ? <Alert type="error" showIcon message={(upsertMutation.error as Error).message} /> : null}
          </Form>
        </div>
      </Modal>
    </>
  );
}
