/** 模块约定：集中维护版本审核状态的中文标签与 Tag 颜色映射；前端页面只能消费这里的展示语义，不能各自写死。 */
/** 与后端 `skill_versions.review_status` 枚举一致。 */
export const REVIEW_STATUS_LABEL_ZH: Record<string, string> = {
  draft: "草稿",
  submitted: "待审核",
  approved: "待发布",
  rejected: "已拒绝",
  published: "已发布",
  archived: "已归档",
};

/** 将版本审核状态码转为界面展示用中文。 */
export function formatReviewStatusLabel(status: string | null | undefined): string {
  if (status == null || status === "") {
    return "未知";
  }
  return REVIEW_STATUS_LABEL_ZH[status] ?? status;
}

/** Tag 颜色：与状态语义一致。 */
export function reviewStatusTagColor(status: string): string {
  switch (status) {
    case "published":
      return "green";
    case "approved":
      return "blue";
    case "submitted":
      return "orange";
    case "rejected":
      return "red";
    case "draft":
      return "default";
    case "archived":
      return "default";
    default:
      return "default";
  }
}
