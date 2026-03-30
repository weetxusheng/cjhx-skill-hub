/** 组件约定：审核中心筛选栏统一承载分类、技能和提交人过滤；保持工作台筛选结构稳定，避免页面容器散落控件。 */
import { Card, Select, Tag } from "antd";

import { AdminFiltersRefreshButton, AdminKeywordSearchCompact } from "../../../components/AdminListToolbar";

export type ReviewsFiltersCardProps = {
  categoryFilter: string | undefined;
  onCategoryChange: (value: string | undefined) => void;
  categoryOptions: { label: string; value: string }[];
  skillDraft: string;
  onSkillDraftChange: (value: string) => void;
  onSkillSearch: () => void;
  creatorDraft: string;
  onCreatorDraftChange: (value: string) => void;
  onCreatorSearch: () => void;
  onRefreshFilters: () => void;
  filteredCount: number;
  apiRowCount: number;
  skillApplied: string;
  canReview: boolean;
};

export function ReviewsFiltersCard({
  categoryFilter,
  onCategoryChange,
  categoryOptions,
  skillDraft,
  onSkillDraftChange,
  onSkillSearch,
  creatorDraft,
  onCreatorDraftChange,
  onCreatorSearch,
  onRefreshFilters,
  filteredCount,
  apiRowCount,
  skillApplied,
  canReview,
}: ReviewsFiltersCardProps) {
  return (
    <Card id="admin-reviews-filters-card" className="content-card filters-card">
      <div className="admin-list-toolbar">
        <div className="admin-list-toolbar__filters">
          <Select
            allowClear
            placeholder="按分类筛选"
            value={categoryFilter}
            onChange={onCategoryChange}
            className="filters-select"
            options={categoryOptions}
          />
          <AdminKeywordSearchCompact
            value={skillDraft}
            onChange={onSkillDraftChange}
            onSearch={onSkillSearch}
            placeholder="搜索技能名、slug 或版本号"
          />
          <AdminKeywordSearchCompact
            value={creatorDraft}
            onChange={onCreatorDraftChange}
            onSearch={onCreatorSearch}
            placeholder="搜索提交人（服务端筛选）"
          />
          <AdminFiltersRefreshButton onClick={onRefreshFilters} />
          <Tag color="processing">
            待审 {filteredCount}
            {skillApplied ? ` / 接口 ${apiRowCount}` : ""}
          </Tag>
          {!canReview ? <Tag>当前账号仅可查看，不能执行审核</Tag> : null}
        </div>
      </div>
    </Card>
  );
}
