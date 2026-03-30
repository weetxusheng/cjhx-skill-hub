/**
 * 组件约定：
 * - 根据分类 slug 渲染统一图标与底色，保持广场分类卡和技能卡视觉一致。
 * - 只做展示映射，不在组件内决定文案或交互行为。
 */
import type { CSSProperties } from "react";

import { getCategoryIconStyle, getCategoryVisual } from "../lib/categoryVisuals";
import type { CategoryItem, PublicSkillListItem } from "../lib/portalTypes";

export function CategoryIcon({
  category,
  className,
}: {
  category: Pick<CategoryItem | PublicSkillListItem, "name" | "slug"> | { category_name: string; category_slug: string };
  className?: string;
}) {
  const visual = getCategoryVisual(category);
  return (
    <span className={className ?? "category-icon"} style={getCategoryIconStyle(visual) as CSSProperties}>
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        {visual.paths.map((path) => (
          <path key={path} d={path} />
        ))}
      </svg>
    </span>
  );
}
