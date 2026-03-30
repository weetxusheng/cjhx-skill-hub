/** 组件约定：分类治理页的筛选与新建入口固定收口在这里；只负责筛选参数输入与动作触发，不直接维护列表数据。 */
import { Button, Card, Select, Typography } from "antd";

import { AdminFiltersRefreshButton, AdminKeywordSearchCompact } from "../../../components/AdminListToolbar";

export type CategoriesFiltersCardProps = {
  keywordDraft: string;
  onKeywordDraftChange: (value: string) => void;
  onKeywordSearch: () => void;
  visibleFilter: boolean | undefined;
  onVisibleFilterChange: (value: boolean | undefined) => void;
  onRefreshFilters: () => void;
  onOpenCreate: () => void;
  canManage: boolean;
};

export function CategoriesFiltersCard({
  keywordDraft,
  onKeywordDraftChange,
  onKeywordSearch,
  visibleFilter,
  onVisibleFilterChange,
  onRefreshFilters,
  onOpenCreate,
  canManage,
}: CategoriesFiltersCardProps) {
  return (
    <Card id="admin-categories-filters-card" className="content-card filters-card">
      <div className="admin-list-toolbar">
        <div className="admin-list-toolbar__filters">
          <AdminKeywordSearchCompact
            value={keywordDraft}
            onChange={onKeywordDraftChange}
            onSearch={onKeywordSearch}
            placeholder="搜索名称、slug、说明或图标"
          />
          <Select
            allowClear
            className="filters-select"
            placeholder="前台展示"
            value={visibleFilter}
            onChange={(v) => onVisibleFilterChange(v as boolean | undefined)}
            options={[
              { label: "前台显示", value: true },
              { label: "前台隐藏", value: false },
            ]}
          />
          <AdminFiltersRefreshButton onClick={onRefreshFilters} />
        </div>
        <div className="admin-list-toolbar__actions">
          <Button type="primary" onClick={onOpenCreate} disabled={!canManage}>
            新建分类
          </Button>
          {!canManage ? <Typography.Text type="secondary">当前账号没有分类管理权限</Typography.Text> : null}
        </div>
      </div>
    </Card>
  );
}
