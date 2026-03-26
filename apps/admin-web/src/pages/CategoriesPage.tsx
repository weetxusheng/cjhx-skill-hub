import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Alert, Button, Card, Empty, Form, Input, InputNumber, Modal, Popconfirm, Space, Switch, Table, Tag, Typography } from "antd";

import { apiRequest } from "../lib/api";
import { hasPermission } from "../lib/permissions";
import { useAuthStore } from "../store/auth";

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

export function CategoriesPage() {
  const accessToken = useAuthStore((state) => state.accessToken);
  const user = useAuthStore((state) => state.user);
  const queryClient = useQueryClient();
  const [form] = Form.useForm<CategoryFormValue>();
  const [modalOpen, setModalOpen] = useState(false);
  const [editingCategory, setEditingCategory] = useState<CategoryItem | null>(null);
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
      setEditingCategory(null);
      setModalOpen(false);
      form.resetFields();
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (categoryId: string) => apiRequest(`/admin/categories/${categoryId}`, { method: "DELETE", token: accessToken }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["admin-categories"] });
    },
  });

  const openCreate = () => {
    setEditingCategory(null);
    form.setFieldsValue({ name: "", slug: "", icon: null, description: null, sort_order: 0, is_visible: true });
    setModalOpen(true);
  };

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

  return (
    <>
      <Space style={{ marginBottom: 16 }}>
        <Button type="primary" onClick={openCreate} disabled={!canManage}>
          新建分类
        </Button>
        {!canManage ? <Typography.Text type="secondary">当前账号没有分类管理权限</Typography.Text> : null}
      </Space>
      <Card id="admin-categories-table-card" className="content-card">
        {categoriesQuery.isError ? (
          <Alert type="error" showIcon message={(categoriesQuery.error as Error).message} />
        ) : categoriesQuery.data?.length ? (
          <div id="admin-categories-table-container">
            <Table
              rowKey="id"
              pagination={false}
              dataSource={categoriesQuery.data}
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
