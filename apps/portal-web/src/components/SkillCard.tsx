/**
 * 组件约定：
 * - 技能广场卡片只展示公开可见摘要，并把详情打开动作上抛给页面层。
 * - 卡片内不直接执行点赞、收藏或下载请求，避免列表与详情状态分叉。
 */
import { ArrowRightOutlined, DownloadOutlined, LikeOutlined, StarOutlined } from "@ant-design/icons";
import { Button, Card, Typography } from "antd";
import dayjs from "dayjs";

import type { PublicSkillListItem } from "../lib/portalTypes";
import { CategoryIcon } from "./CategoryIcon";

export function SkillCard({ skill, onOpen }: { skill: PublicSkillListItem; onOpen: (slug: string) => void }) {
  return (
    <Card key={skill.id} className="skill-card" variant="borderless" hoverable onClick={() => onOpen(skill.slug)}>
      <div className="skill-card-topline">
        <div className="skill-card-heading">
          <CategoryIcon category={{ name: skill.category_name, slug: skill.category_slug }} className="skill-category-icon" />
          <div>
            <div className="skill-card-category-name">{skill.category_name}</div>
            <div className="skill-card-date">{skill.published_at ? dayjs(skill.published_at).format("YYYY-MM-DD") : "未发布"}</div>
          </div>
        </div>
        <span className="skill-version-pill">v{skill.latest_version_no ?? "-"}</span>
      </div>
      <Typography.Title level={4} className="skill-title">
        {skill.name}
      </Typography.Title>
      <Typography.Paragraph className="skill-summary">{skill.summary}</Typography.Paragraph>
      <div className="skill-stats">
        <span>
          <DownloadOutlined />
          下载 {skill.download_count}
        </span>
        <span>
          <StarOutlined />
          收藏 {skill.favorite_count}
        </span>
        <span>
          <LikeOutlined />
          点赞 {skill.like_count}
        </span>
      </div>
      <Button
        block
        className="portal-secondary-button skill-card-button"
        onClick={(event) => {
          event.stopPropagation();
          onOpen(skill.slug);
        }}
      >
        查看详情
        <ArrowRightOutlined />
      </Button>
    </Card>
  );
}
