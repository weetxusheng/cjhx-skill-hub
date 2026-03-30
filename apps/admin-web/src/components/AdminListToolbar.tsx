/** 组件约定：后台列表筛选栏的关键字搜索与刷新动作统一复用这里，保证筛选控件高度、按钮语义和交互反馈一致。 */
import { ReloadOutlined } from "@ant-design/icons";
import { Button, Input, Space, Tooltip } from "antd";

export type AdminKeywordSearchCompactProps = {
  value: string;
  onChange: (value: string) => void;
  onSearch: () => void;
  placeholder?: string;
  className?: string;
};

/**
 * 列表页关键字筛选：输入框右侧独立「搜索」按钮，与「刷新」配合使用。
 */
export function AdminKeywordSearchCompact({ value, onChange, onSearch, placeholder, className }: AdminKeywordSearchCompactProps) {
  return (
    <Space.Compact className={className ?? "filters-keyword-compact"}>
      <Input value={value} placeholder={placeholder} allowClear onChange={(event) => onChange(event.target.value)} onPressEnter={onSearch} />
      <Button type="primary" onClick={onSearch}>
        搜索
      </Button>
    </Space.Compact>
  );
}

export type AdminFiltersRefreshButtonProps = {
  onClick: () => void;
  loading?: boolean;
};

/**
 * 清除所有筛选并重新拉取列表数据（由各页在 onClick 内重置 state + invalidate）。
 */
export function AdminFiltersRefreshButton({ onClick, loading }: AdminFiltersRefreshButtonProps) {
  return (
    <Tooltip title="清除所有筛选并重新加载列表">
      <Button icon={<ReloadOutlined />} onClick={onClick} loading={loading}>
        刷新
      </Button>
    </Tooltip>
  );
}
