/**
 * 模块约定：
 * - 汇总技能分类对应的颜色、图标和展示语义，作为前台视觉映射的唯一来源。
 * - 新增分类时先补这里，再补组件和样式，不在页面里散落视觉常量。
 */
import type { CSSProperties } from "react";

import type { CategoryItem, PublicSkillListItem } from "./portalTypes";

type CategoryVisual = {
  color: string;
  background: string;
  border: string;
  paths: string[];
};

const CATEGORY_VISUALS: Record<string, CategoryVisual> = {
  "ai-intelligence": {
    color: "#007AFF",
    background: "rgba(0, 122, 255, 0.14)",
    border: "rgba(0, 122, 255, 0.22)",
    paths: [
      "M12 5a3 3 0 1 0-5.997.125 4 4 0 0 0-2.526 5.77 4 4 0 0 0 .556 6.588A4 4 0 1 0 12 18Z",
      "M12 5a3 3 0 1 1 5.997.125 4 4 0 0 1 2.526 5.77 4 4 0 0 1-.556 6.588A4 4 0 1 1 12 18Z",
      "M15 13a4.5 4.5 0 0 1-3-4 4.5 4.5 0 0 1-3 4",
      "M17.599 6.5a3 3 0 0 0 .399-1.375",
      "M6.003 5.125A3 3 0 0 0 6.401 6.5",
      "M3.477 10.896a4 4 0 0 1 .585-.396",
      "M19.938 10.5a4 4 0 0 1 .585.396",
      "M6 18a4 4 0 0 1-1.967-.516",
      "M19.967 17.484A4 4 0 0 1 18 18",
    ],
  },
  "developer-tools": {
    color: "#5856D6",
    background: "rgba(88, 86, 214, 0.14)",
    border: "rgba(88, 86, 214, 0.22)",
    paths: ["m18 16 4-4-4-4", "m6 8-4 4 4 4", "m14.5 4-5 16"],
  },
  productivity: {
    color: "#34C759",
    background: "rgba(52, 199, 89, 0.14)",
    border: "rgba(52, 199, 89, 0.22)",
    paths: [
      "M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z",
      "m12 15-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z",
      "M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0",
      "M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5",
    ],
  },
  "data-analysis": {
    color: "#FF9500",
    background: "rgba(255, 149, 0, 0.14)",
    border: "rgba(255, 149, 0, 0.22)",
    paths: ["M3 3v16a2 2 0 0 0 2 2h16", "M18 17V9", "M13 17V5", "M8 17v-3"],
  },
  "content-creation": {
    color: "#FF2D55",
    background: "rgba(255, 45, 85, 0.14)",
    border: "rgba(255, 45, 85, 0.22)",
    paths: [
      "M15.707 21.293a1 1 0 0 1-1.414 0l-1.586-1.586a1 1 0 0 1 0-1.414l5.586-5.586a1 1 0 0 1 1.414 0l1.586 1.586a1 1 0 0 1 0 1.414z",
      "m18 13-1.375-6.874a1 1 0 0 0-.746-.776L3.235 2.028a1 1 0 0 0-1.207 1.207L5.35 15.879a1 1 0 0 0 .776.746L13 18",
      "m2.3 2.3 7.286 7.286",
      "M11 11m-2 0a2 2 0 1 0 4 0a2 2 0 1 0 -4 0",
    ],
  },
  "security-compliance": {
    color: "#32ADE6",
    background: "rgba(50, 173, 230, 0.14)",
    border: "rgba(50, 173, 230, 0.22)",
    paths: ["M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"],
  },
  "communication-collaboration": {
    color: "#30D158",
    background: "rgba(48, 209, 88, 0.14)",
    border: "rgba(48, 209, 88, 0.22)",
    paths: ["M7.9 20A9 9 0 1 0 4 16.1L2 22Z"],
  },
};

const CATEGORY_VISUALS_BY_NAME: Record<string, string> = {
  "AI 智能": "ai-intelligence",
  开发工具: "developer-tools",
  效率提升: "productivity",
  数据分析: "data-analysis",
  内容创作: "content-creation",
  安全合规: "security-compliance",
  通讯协作: "communication-collaboration",
};

export function getCategoryVisual(
  category: Pick<CategoryItem | PublicSkillListItem, "name" | "slug"> | { category_name: string; category_slug: string },
): CategoryVisual {
  const slug = "slug" in category ? category.slug : category.category_slug;
  const name = "name" in category ? category.name : category.category_name;
  return CATEGORY_VISUALS[slug] ?? CATEGORY_VISUALS[CATEGORY_VISUALS_BY_NAME[name]] ?? CATEGORY_VISUALS.productivity;
}

export function getCategoryIconStyle(visual: CategoryVisual) {
  return {
    "--icon-color": visual.color,
    "--icon-bg": visual.background,
    "--icon-border": visual.border,
  } as CSSProperties;
}
