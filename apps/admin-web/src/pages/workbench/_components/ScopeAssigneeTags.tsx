/**
 * 组件约定：
 * - 负责把审核/发布负责人渲染成标签列表。
 * - 仅在角色标签上提供 hover 成员提示，用户标签保持普通展示。
 * - 空数据时返回统一的次级文案，避免列表列空白。
 */
import { Space, Tag, Tooltip, Typography } from "antd";

export type ScopeAssigneeItem = {
  target_id: string;
  target_type: "user" | "role";
  target_name: string;
  members: string[];
};

function renderRoleTooltip(item: ScopeAssigneeItem) {
  if (!item.members.length) {
    return (
      <div>
        <Typography.Text>当前角色下暂无成员</Typography.Text>
      </div>
    );
  }
  return (
    <div>
      <Typography.Text strong style={{ color: '#1677ff' }}>{item.target_name}</Typography.Text>
      <div>{item.members.join("、")}</div>
    </div>
  );
}

export function ScopeAssigneeTags({
  items,
  emptyText = "未配置",
}: {
  items: ScopeAssigneeItem[] | null | undefined;
  emptyText?: string;
}) {
  const assignees = items ?? [];
  if (!assignees.length) {
    return <Typography.Text type="secondary">{emptyText}</Typography.Text>;
  }

  return (
    <Space size={[8, 8]} wrap>
      {assignees.map((item) =>
        item.target_type === "role" ? (
          <Tooltip key={`${item.target_type}-${item.target_id}`} title={renderRoleTooltip(item)}>
            <Tag color="blue" className="scope-assignee-tag scope-assignee-tag--role">
              {item.target_name}
            </Tag>
          </Tooltip>
        ) : (
          <Tag key={`${item.target_type}-${item.target_id}`} className="scope-assignee-tag">
            {item.target_name}
          </Tag>
        ),
      )}
    </Space>
  );
}
