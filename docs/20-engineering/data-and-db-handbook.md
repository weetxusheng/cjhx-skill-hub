# 数据与数据库手册

## 目的
本手册统一 Skill Hub 的表设计、字段规范、索引与约束、migration/seed 手册，以及核心表规格示例。数据结构相关事实以这里为主。

## 命名与通用字段
### 命名
- 表名：复数蛇形，如 `skill_versions`。
- 主键：统一 `id`，推荐 UUID。
- 索引：`idx_<table>_<field...>`
- 唯一约束：`uq_<table>_<field...>`
- 外键：`fk_<from_table>_<to_table>_<field>`

### 通用字段
- `id`：UUID 主键。
- `created_at` / `updated_at`：时区感知时间；`updated_at` 必须有自动刷新机制。
- `status`：用于主档存活态，不承载复杂状态机。
- `remark` / `comment`：面向人工说明，禁止承载结构化业务事实。
- `operator` / `snapshot`：仅用于审计、历史或变更留痕。

## 表设计原则
- 明细事实优先建表，聚合字段作为冗余缓存存在。
- 冗余计数必须能从明细表追溯，且明确刷新时机。
- 外键、唯一约束、检查约束优先落数据库，不依赖应用层约定。
- 列表热点查询需要明确索引策略，不能事后补救。
- 状态机涉及的关键唯一性应落数据库，例如单 skill 仅一个 `published` 版本。

## 冗余统计与明细表
- `like_count`、`favorite_count`、`download_count` 属于冗余汇总字段。
- `skill_likes`、`favorites`、`download_logs` 属于事实明细表。
- 能容忍最终一致时可异步更新；当前 Skill Hub 默认关键互动计数与写入同事务或同业务动作同步更新。
- 统计接口展示趋势时，必须说明时间窗口、粒度和刷新方式。

## 核心表规格
### `skills`
- 职责：skill 主档、公开展示字段、线上版本指针与聚合计数。
- 关键字段：
  - `slug`：全局唯一
  - `category_id`
  - `current_published_version_id`
  - `latest_version_no`
  - `status`
  - `favorite_count / like_count / download_count`
- 约束：
  - `slug` 唯一
  - 被引用分类不可删除

### `skill_versions`
- 职责：版本正文、manifest、usage guide、审核状态与发布状态。
- 关键字段：
  - `skill_id`
  - `version`
  - `review_status`
  - `review_comment`
  - `readme_markdown`
  - `manifest_json`
  - `usage_guide_json`
  - `created_by`
  - `published_at`
- 约束：
  - 同一 skill 内版本号唯一
  - 单 skill 只能有一个 `published`

### `version_reviews`
- 职责：审核、发布、归档、回滚等关键动作记录。
- 关键字段：
  - `skill_version_id`
  - `action`
  - `comment`
  - `operator_user_id`
  - `created_at`

### `audit_logs`
- 职责：后台写操作审计。
- 关键字段：
  - `actor_user_id`
  - `action`
  - `target_type`
  - `target_id`
  - `before_snapshot`
  - `after_snapshot`
  - `request_id`

### `skill_role_grants` / `skill_user_grants`
- 职责：skill 级授权对象与 scope。
- 关键字段：
  - `skill_id`
  - `role_id` 或 `user_id`
  - `permission_scope`
- 约束：
  - 同一 `skill + target + scope` 不重复

### 互动与下载明细
- `favorites`：`user_id + skill_id` 唯一。
- `skill_likes`：`user_id + skill_id` 唯一。
- `download_logs`：记录下载事实，可做脱敏展示与趋势分析。

## Migration 手册
### 新增业务表
- 先定义职责、主键、外键、唯一约束、索引，再写 migration。
- 同步补模型、schema、最小回归测试。

### 线上表加字段
- 明确默认值、历史数据回填策略与是否允许为空。
- 若字段参与筛选或排序，必须同步评估索引。

### 补索引
- 优先针对真实查询路径补复合索引。
- 在线上表补索引时，文档需说明目标查询与预期收益。

### 调整状态机或约束
- 先更新正式规范，再更新 migration 与测试。
- 涉及唯一性、检查约束或枚举值变化时，必须补冲突与回滚场景测试。

## Seed 与测试数据规则
- migration 只保留系统初始化必需数据，如默认角色、管理员、基础分类。
- 演示/联调数据走单独 seed 脚本，不混入 schema migration。
- 测试优先动态创建最小数据集，不依赖共享脏数据。
- seed、测试、生产数据结构必须使用同一套表事实，不允许“演示专用假结构”。

## Schema 变更 Checklist
- 是否更新 migration
- 是否更新模型与 schema
- 是否更新架构/流程文档
- 是否评估索引与约束
- 是否补种子或测试数据
- 是否补权限、统计或状态机回归测试
- 是否补 release-check 所需验证
