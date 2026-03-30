/**
 * 模块约定：
 * - 汇总后台技能详情页相关的前端类型契约，字段命名与后端响应保持一致。
 * - 这里只放类型，不放默认值、格式化逻辑或请求函数。
 */
export type SkillVersionSummary = {
  id: string;
  version: string;
  review_status: string;
  created_at: string;
  published_at: string | null;
};

export type ReviewRecordItem = {
  id: string;
  action: string;
  comment: string;
  operator_display_name: string;
  created_at: string;
};

export type DepartmentBrief = {
  id: string;
  name: string;
};

export type SkillGrantItem = {
  id: string;
  target_type: "role" | "user";
  target_id: string;
  target_name: string;
  /** 用户授权时关联 departments；角色授权为 null。 */
  target_primary_department?: DepartmentBrief | null;
  permission_scope: "owner" | "maintainer" | "reviewer" | "publisher" | "rollback" | "viewer";
  created_at: string;
};

export type SkillStatsOverview = {
  skill_id: string;
  like_count: number;
  favorite_count: number;
  download_count: number;
  recent_downloads: Array<{ day: string; count: number }>;
  recent_favorites: Array<{ day: string; count: number }>;
  recent_likes: Array<{ day: string; count: number }>;
};

export type SkillFavoriteRecord = {
  user_id: string;
  username: string;
  display_name: string;
  created_at: string;
};

export type SkillDownloadRecord = {
  id: string;
  user_id: string | null;
  username: string | null;
  display_name: string | null;
  version: string;
  created_at: string;
  ip: string | null;
  user_agent: string | null;
};

export type SkillDetailResponse = {
  skill: {
    id: string;
    name: string;
    slug: string;
    summary: string;
    description: string;
    status: string;
    category_name: string;
    category_slug: string;
    latest_version_no: string | null;
    current_published_version_id: string | null;
    owner_user_id: string;
    owner_display_name: string | null;
    download_count: number;
    favorite_count: number;
    like_count: number;
    published_at: string | null;
  };
  versions: SkillVersionSummary[];
  recent_reviews: ReviewRecordItem[];
  latest_version_status: string | null;
  current_published_version: string | null;
  pending_review_count: number;
  pending_release_count: number;
  capabilities: {
    edit_skill: boolean;
    upload_version: boolean;
    manage_grants: boolean;
    view_favorite_details: boolean;
    view_download_details: boolean;
    view_sensitive_download_details: boolean;
  };
};

export type CategoryItem = {
  id: string;
  name: string;
  slug: string;
};

export type RoleItem = {
  id: string;
  code: string;
  name: string;
  is_active: boolean;
};

export type UserItem = {
  id: string;
  username: string;
  display_name: string;
  primary_department?: DepartmentBrief | null;
  status: "active" | "disabled";
};

export type SkillUpdateInput = {
  name: string;
  summary: string;
  description: string;
  category_slug: string;
};

export const SCOPE_OPTIONS = [
  { label: "负责人", value: "owner" },
  { label: "维护者", value: "maintainer" },
  { label: "审核员", value: "reviewer" },
  { label: "发布员", value: "publisher" },
  { label: "回滚", value: "rollback" },
  { label: "查看者", value: "viewer" },
];
