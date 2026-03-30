/**
 * 模块约定：
 * - 汇总版本详情页/弹窗共用的类型、动作配置与文案输入结构，避免两个入口重复维护。
 * - 这里只放共享契约，不放页面级查询、副作用或 React 状态。
 */
export type UsageGuideFields = {
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

export type VersionDetailResponse = {
  skill: {
    id: string;
    name: string;
    slug: string;
    category_name: string;
    category_slug: string;
    current_published_version_id: string | null;
  };
  version: {
    id: string;
    version: string;
    manifest_json: Record<string, unknown>;
    usage_guide_json: UsageGuideFields;
    readme_markdown: string;
    readme_html: string;
    changelog: string;
    install_notes: string;
    breaking_changes: string;
    source_type: string;
    review_status: string;
    review_comment: string | null;
    published_at: string | null;
    created_at: string;
  };
  reviews: Array<{
    id: string;
    action: string;
    comment: string;
    operator_display_name: string;
    created_at: string;
  }>;
  capabilities: {
    edit_content: boolean;
    submit: boolean;
    approve: boolean;
    reject: boolean;
    publish: boolean;
    archive: boolean;
    rollback: boolean;
    download_package: boolean;
  };
};

export type UpdateVersionContentInput = {
  changelog: string;
  install_notes: string;
  breaking_changes: string;
  readme_markdown: string;
  usage_guide_json: UsageGuideFields;
};

export type VersionActionKey = "submit" | "approve" | "reject" | "publish" | "archive" | "rollback";

type ActionConfig = {
  endpoint: string;
  title: string;
  description: string;
  required?: boolean;
};

export const ACTION_CONFIG: Record<VersionActionKey, ActionConfig> = {
  submit: { endpoint: "submit", title: "提交审核", description: "可选填写提交说明，提交后版本将进入待审队列。" },
  approve: { endpoint: "approve", title: "审核通过", description: "确认通过当前版本审核，可选填写说明。" },
  reject: { endpoint: "reject", title: "拒绝版本", description: "拒绝原因会记录到审核历史中。", required: true },
  publish: { endpoint: "publish", title: "发布版本", description: "发布后旧的 published 版本会自动归档。" },
  archive: { endpoint: "archive", title: "归档版本", description: "归档后前台将不再展示该版本。", required: false },
  rollback: { endpoint: "rollback", title: "回滚发布", description: "请填写回滚说明，该版本会重新成为当前发布版本。", required: true },
};
