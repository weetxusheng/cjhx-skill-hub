/**
 * 组件约定：
 * - 负责 skill 级授权对象的新增、删除与只读展示，不承担全局角色管理。
 * - 授予失败与删除失败分别在组件内展示，外层页面只负责提供数据和 mutation 回调。
 */
import { Alert, Button, Card, Popconfirm, Select, Space, Table, Tag, Typography } from "antd";
import dayjs from "dayjs";

import { formatSkillScopeLabel } from "../../../lib/skillScopeLabels";
import { SCOPE_OPTIONS, type SkillGrantItem } from "../skillDetailTypes";

type SelectOption = {
  label: string;
  value: string;
};

type SkillGrantsCardProps = {
  canManageGrants: boolean;
  deleteErrorMessage: string | null;
  grants: SkillGrantItem[];
  isDeletingGrant: boolean;
  isGrantingRoles: boolean;
  isGrantingUsers: boolean;
  onDeleteGrant: (grantId: string, targetType: "role" | "user") => void;
  onGrantRoles: () => void;
  onGrantUsers: () => void;
  onRoleScopeChange: (value: string) => void;
  onRoleSelectionChange: (value: string[]) => void;
  onUserScopeChange: (value: string) => void;
  onUserSelectionChange: (value: string[]) => void;
  roleGrantErrorMessage: string | null;
  roleOptions: SelectOption[];
  roleScope: string;
  selectedRoleIds: string[];
  selectedUserIds: string[];
  userGrantErrorMessage: string | null;
  userOptions: SelectOption[];
  userScope: string;
};

/**
 * 技能详情 - 按角色/用户授予 skill 级权限
 *
 * - `canManageGrants` 为 false 时隐藏授予与删除操作，表格可只读展示。
 * - 角色/用户授予分别使用 `roleScope`/`userScope` 与多选；错误信息分开展示以便定位接口失败原因。
 */
export function SkillGrantsCard({
  canManageGrants,
  deleteErrorMessage,
  grants,
  isDeletingGrant,
  isGrantingRoles,
  isGrantingUsers,
  onDeleteGrant,
  onGrantRoles,
  onGrantUsers,
  onRoleScopeChange,
  onRoleSelectionChange,
  onUserScopeChange,
  onUserSelectionChange,
  roleGrantErrorMessage,
  roleOptions,
  roleScope,
  selectedRoleIds,
  selectedUserIds,
  userGrantErrorMessage,
  userOptions,
  userScope,
}: SkillGrantsCardProps) {
  return (
    <Card id="admin-skill-detail-grants-card" className="content-card detail-card detail-card--stretch" title="授权对象">
      <Space direction="vertical" size={16} style={{ width: "100%" }}>
        <Space wrap>
          <Select value={roleScope} onChange={onRoleScopeChange} options={SCOPE_OPTIONS} style={{ width: 160 }} />
          <Select
            mode="multiple"
            placeholder="给角色授权"
            value={selectedRoleIds}
            onChange={onRoleSelectionChange}
            style={{ minWidth: 280 }}
            options={roleOptions}
            disabled={!canManageGrants}
          />
          <Button type="primary" onClick={onGrantRoles} disabled={!canManageGrants || !selectedRoleIds.length} loading={isGrantingRoles}>
            授予角色
          </Button>
        </Space>

        <Space wrap>
          <Select value={userScope} onChange={onUserScopeChange} options={SCOPE_OPTIONS} style={{ width: 160 }} />
          <Select
            mode="multiple"
            placeholder="给指定用户授权"
            value={selectedUserIds}
            onChange={onUserSelectionChange}
            style={{ minWidth: 280 }}
            options={userOptions}
            disabled={!canManageGrants}
          />
          <Button type="primary" onClick={onGrantUsers} disabled={!canManageGrants || !selectedUserIds.length} loading={isGrantingUsers}>
            授予用户
          </Button>
        </Space>

        {!canManageGrants ? <Typography.Text type="secondary">只有该技能的 owner 才能配置授权对象。</Typography.Text> : null}
        {roleGrantErrorMessage ? <Alert type="error" showIcon message={roleGrantErrorMessage} /> : null}
        {userGrantErrorMessage ? <Alert type="error" showIcon message={userGrantErrorMessage} /> : null}
        {deleteErrorMessage ? <Alert type="error" showIcon message={deleteErrorMessage} /> : null}

        <div id="admin-skill-detail-grants-table-container">
          <Table
            rowKey="id"
            pagination={false}
            dataSource={grants}
            columns={[
              { title: "类型", dataIndex: "target_type", render: (value: string) => <Tag>{value === "role" ? "角色" : "用户"}</Tag> },
              { title: "对象", dataIndex: "target_name" },
              {
                title: "一级部门",
                dataIndex: "target_primary_department",
                render: (_: unknown, record: SkillGrantItem) =>
                  record.target_type === "user" ? (record.target_primary_department?.name ?? "—") : "—",
              },
              {
                title: "授权范围",
                dataIndex: "permission_scope",
                render: (value: string) => <Tag color="blue">{formatSkillScopeLabel(value)}</Tag>,
              },
              { title: "授权时间", dataIndex: "created_at", render: (value: string) => dayjs(value).format("YYYY-MM-DD HH:mm") },
              {
                title: "操作",
                render: (_value: unknown, record: SkillGrantItem) => (
                  <Popconfirm
                    title="移除授权"
                    description="移除后，该对象会立即失去这个 skill 上对应的操作范围。"
                    okButtonProps={{ loading: isDeletingGrant }}
                    onConfirm={() => onDeleteGrant(record.id, record.target_type)}
                  >
                    <Button
                      size="small"
                      danger
                      disabled={!canManageGrants}
                      loading={isDeletingGrant}
                    >
                      移除
                    </Button>
                  </Popconfirm>
                ),
              },
            ]}
          />
        </div>
      </Space>
    </Card>
  );
}
