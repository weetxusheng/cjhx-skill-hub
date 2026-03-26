# 数据库与 Migration 规范

## 基本规则
- 所有结构变更必须有 Alembic migration
- migration 与模型变更必须同一轮提交
- 新字段上线前要考虑：
  - 旧数据兼容
  - seed 数据更新
  - 测试 fixture 更新

## Migration 命名
- 命名格式：`00xx_<verb>_<topic>.py`
- 动词建议：
  - `create`
  - `add`
  - `update`
  - `backfill`
  - `drop`

## Schema 变更 Checklist
1. 模型是否同步更新
2. Alembic 是否同步更新
3. 是否需要默认值或数据回填
4. 是否需要索引
5. 是否需要外键 / 唯一约束 / check 约束
6. 是否会影响现有 seed
7. 是否会影响现有测试

## 当前重点表
- `skill_versions`：版本状态与发布指引
- `skill_role_grants` / `skill_user_grants`：skill 级授权
- `version_reviews`：审核与发布动作链
- `favorites` / `skill_likes` / `download_logs`：互动与分发明细

## 约束要求
- 一个 skill 同时只能有一个 `published` 版本
- `(skill_id, version)` 必须唯一
- 用户级收藏、点赞去重
- 新增授权表必须有外键与范围 check 约束

## 索引与外键要求
- 工作台高频过滤字段必须有索引
- 明细表必须保留到主档/版本/用户的可追溯外键
- 审核、发布、统计相关表禁止“软约束不落库”

## Seed 规范
- 基础 seed 和演示 seed 分开
- 基础 seed 至少包括：
  - 默认角色
  - 默认权限
  - 管理员账号
  - 分类
- 演示 seed 至少包括：
  - 待审核
  - 待发布
  - 已发布
  - 已拒绝
  - 已归档
  - 已回滚

## 初始化 SQL
- 仓库需保留一份可迁移环境使用的数据库初始化 SQL：`infra/sql/skill-hub-init.sql`
- 导出命令统一使用：`pnpm db:export-init-sql`
- 生成方式必须基于“临时空库执行到 Alembic head 后再导出”，不能直接从本地脏数据或联调库手工 dump
- 当 migration、基础 seed、权限点、默认角色或关键约束变化时，要同步更新这份 SQL

## 冗余统计一致性
- 明细表是事实来源
- `skills.favorite_count`、`skills.like_count`、`skills.download_count` 是读取优化字段
- 任何统计写入逻辑变更都要验证“明细汇总 == 冗余字段”

## 测试要求
- migration 从空库到 head 必须可执行
- 新 seed 数据必须与测试 fixture 兼容
- 统计与授权表新增后，要至少补一条针对性回归测试
