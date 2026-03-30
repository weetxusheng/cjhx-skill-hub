/** 模块约定：统一 skill 级授权 scope 的中文展示，避免详情页、授权表格和弹窗各自维护一套翻译。 */
/** Skill 级 permission_scope 中文展示（与后端枚举一致）。 */
export const SKILL_SCOPE_LABEL_ZH: Record<string, string> = {
  owner: "负责人",
  maintainer: "维护者",
  reviewer: "审核员",
  publisher: "发布员",
  rollback: "回滚",
  viewer: "查看者",
};

export function formatSkillScopeLabel(code: string): string {
  return SKILL_SCOPE_LABEL_ZH[code] ?? code;
}
