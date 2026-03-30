/**
 * 模块约定：
 * - 统一处理 usage guide 的默认值、兜底文案和前台展示需要的整理逻辑。
 * - 详情页和上传链路都通过这里消费，不在组件内重复拼装 guide 结构。
 */
import { API_BASE_URL } from "./api";
import type { PublicSkillDetailResponse, UsageGuideValue } from "./portalTypes";

function buildFallbackUsageGuide(detail: PublicSkillDetailResponse): UsageGuideValue {
  const downloadUrl = `${API_BASE_URL}/public/skills/${detail.skill.id}/download`;
  const installNotes = detail.current_version.install_notes || "按 README 指引完成安装与配置。";
  return {
    agent: {
      standard_prompt: `请帮我使用 Skill Hub 技能“${detail.skill.name}”（slug: ${detail.skill.slug}）。先通过 ${downloadUrl} 下载当前已发布版本，阅读 README 和安装说明，然后按技能用途执行。`,
      accelerated_prompt: `请优先使用 Skill Hub 平台接口下载技能“${detail.skill.name}”（slug: ${detail.skill.slug}），固定使用当前 published 版本；下载地址为 ${downloadUrl}。下载后先阅读 README，再根据安装说明执行。`,
    },
    human: {
      standard_command: `curl -L "${downloadUrl}" -o "${detail.skill.slug}.zip"`,
      accelerated_command: `curl --retry 3 --retry-delay 2 -L "${downloadUrl}" -o "${detail.skill.slug}.zip"`,
      post_install_command: `unzip -o "${detail.skill.slug}.zip" -d "./${detail.skill.slug}" && cd "./${detail.skill.slug}" && printf "%s\\n" "${installNotes}"`,
    },
  };
}

export function resolveUsageGuide(detail: PublicSkillDetailResponse): UsageGuideValue {
  const usageGuide = detail.usage_guide;
  if (
    usageGuide &&
    usageGuide.agent &&
    usageGuide.human &&
    typeof usageGuide.agent.standard_prompt === "string" &&
    typeof usageGuide.agent.accelerated_prompt === "string" &&
    typeof usageGuide.human.standard_command === "string" &&
    typeof usageGuide.human.accelerated_command === "string" &&
    typeof usageGuide.human.post_install_command === "string"
  ) {
    return usageGuide;
  }
  return buildFallbackUsageGuide(detail);
}
