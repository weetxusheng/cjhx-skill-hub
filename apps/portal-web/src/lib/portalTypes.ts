/**
 * 模块约定：
 * - 汇总前台列表、详情、上传记录、会话等共享类型契约，字段名与 API 响应保持一致。
 * - 这里只放类型，不放默认值、转换器和业务副作用。
 */
export type CategoryItem = {
  id: string;
  name: string;
  slug: string;
  icon: string | null;
  description: string | null;
  sort_order: number;
  is_visible: boolean;
  skill_count: number;
};

export type PublicSkillListItem = {
  id: string;
  name: string;
  slug: string;
  summary: string;
  category_name: string;
  category_slug: string;
  latest_version_no: string | null;
  download_count: number;
  favorite_count: number;
  like_count: number;
  published_at: string | null;
  icon_file_id: string | null;
};

export type PortalUploadRecordItem = {
  version_id: string;
  skill_id: string;
  skill_name: string;
  skill_slug: string;
  category_name: string;
  category_slug: string;
  version: string;
  review_status: string;
  review_comment: string | null;
  published_at: string | null;
  created_at: string;
  updated_at: string;
};

export type PagedResponse<T> = {
  items: T[];
  total: number;
  page: number;
  page_size: number;
};

export type PublicSkillDetailResponse = {
  skill: {
    id: string;
    name: string;
    slug: string;
    summary: string;
    description: string;
    category_name: string;
    category_slug: string;
    latest_version_no: string | null;
    download_count: number;
    favorite_count: number;
    like_count: number;
    published_at: string | null;
  };
  current_version: {
    id: string;
    version: string;
    readme_markdown: string;
    readme_html: string;
    changelog: string;
    install_notes: string;
    breaking_changes: string;
    published_at: string | null;
  };
  published_versions: Array<{
    id: string;
    version: string;
    review_status: string;
    created_at: string;
    published_at: string | null;
  }>;
  is_favorited: boolean;
  is_liked: boolean;
  usage_guide: {
    agent: {
      standard_prompt: string;
      accelerated_prompt: string;
    };
    human: {
      standard_command: string;
      accelerated_command: string;
      post_install_command: string;
    };
  };
};

export type UsageGuideValue = {
  agent: {
    standard_prompt: string;
    accelerated_prompt: string;
  };
  human: {
    standard_command: string;
    accelerated_command: string;
    post_install_command: string;
  };
};

export type PortalUser = {
  id: string;
  username: string;
  display_name: string;
  email: string | null;
  status: "active" | "disabled";
  roles: string[];
  permissions: string[];
};

export type LoginResponse = {
  access_token: string;
  refresh_token: string;
  user: PortalUser;
};
