# Skill Hub Master Plan

更新时间：2026-03-25 16:12 CST

> 本文件只记录阶段计划、历史演进和进度状态，不作为当前架构、权限、审核流和仓库结构的正式事实来源。
> 当前行为以 `docs/10-architecture/`、`docs/20-engineering/`、`docs/30-product-flows/` 为准。

## 1. 项目目标与完成定义

### 1.1 项目目标
在 `/Users/xusheng/Documents/project/cjhx-skill-hub` 从空仓开始建设一个企业级 Skill 广场系统，形成完整的产品与工程闭环。系统必须同时包含以下能力：

- 前台 Skill 广场：
  - `/categories` 主页面
  - 分类胶囊筛选
  - 关键词搜索
  - 排序
  - 技能卡片网格
  - 分页
  - 技能详情抽屉
  - 收藏
  - 下载
- 后台管理端：
  - 登录
  - Dashboard
  - 技能列表
  - 技能详情
  - 版本详情
  - 上传技能包
  - 新版本上传
  - 提交审核
  - 审核通过/拒绝
  - 发布
  - 归档
  - 回滚发布
  - 分类管理
  - 用户管理
  - 审计日志
- 后端业务服务：
  - 认证
  - RBAC
  - ZIP 包校验与解包
  - Skill 元数据管理
  - 版本状态机
  - 收藏/下载统计
  - 审计日志
  - 对象存储集成
- 数据层：
  - 完整 PostgreSQL 表结构
  - Alembic 迁移
  - 真实 SQL 约束、索引、触发器
  - 初始化种子数据
- 交付能力：
  - 本地开发环境
  - 本地 PostgreSQL 运行环境
  - 测试脚本
  - 部署说明

### 1.2 完成定义
以下条件全部满足才算项目完成：

- 前台 `portal-web` 与后台 `admin-web` 可正常启动并接入真实 API。
- 数据库所有核心表、外键、约束、索引、触发器、扩展均以 Alembic migration 落地。
- 后端所有主流程 API 完成并通过最小集成验证。
- Skill ZIP 上传、解包、解析、落盘、提审、审核、发布、回滚全链路可跑通。
- 前台只能看到 `published` 版本，后台能看到完整版本历史。
- 收藏、下载、审计、权限控制均生效。
- 对象存储可上传并返回预签名下载链接。
- 具备至少一套本地初始化脚本和部署说明。
- 主计划文件作为人工与 Codex 接力时的唯一事实来源，进度可持续更新。

### 1.3 非目标
以下内容明确不做，避免实现范围继续漂移：

- 企业 SSO / LDAP / OAuth 企业身份接入
- 自动安全机审引擎
- 评论系统
- 评分系统
- 在线安装执行能力
- 多语言国际化
- 多租户隔离
- 多级树形分类
- 外部公开开放平台 API

## 2. 技术与目录决策

### 2.1 技术栈

#### 前端
- `React 18`
- `TypeScript`
- `Vite`
- `React Router`
- `Ant Design`
- `TanStack Query`
- `Zustand`
- `Axios`
- `dayjs`

#### 后端
- `Python 3.14`
- `FastAPI`
- `SQLAlchemy 2.x`
- `Pydantic v2`
- `Alembic`
- `psycopg`
- `redis-py`
- `python-jose` 或 `PyJWT`
- `argon2-cffi`
- `boto3`
- `python-multipart`
- `PyYAML`
- `markdown-it-py` + HTML 白名单清洗

#### 基础设施
- `PostgreSQL 16`
- `Redis 7`
- `MinIO`
- 本地进程运行模式

### 2.2 仓库目录
固定目录结构如下：

```text
/Users/xusheng/Documents/project/cjhx-skill-hub
├── apps
│   ├── portal-web
│   ├── admin-web
│   └── api-server
├── docs
│   └── skill-hub-master-plan.md
├── infra
│   └── scripts
└── .env.example
```

### 2.3 应用职责
- `apps/portal-web`
  - 面向普通用户的 Skill 广场
  - 只暴露 `/categories`
  - 所有数据来自 `/api/public/*`
- `apps/admin-web`
  - 面向内部运营/审核/发布/管理员
  - 所有后台操作来自 `/api/admin/*`
- `apps/api-server`
  - 提供认证、公共查询、后台管理、上传下载、审计

### 2.4 环境变量规范
必须统一整理到根目录 `.env.example`，至少包含：

- `POSTGRES_HOST`
- `POSTGRES_PORT`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `REDIS_URL`
- `S3_ENDPOINT`
- `S3_ACCESS_KEY`
- `S3_SECRET_KEY`
- `S3_BUCKET`
- `JWT_SECRET`
- `JWT_ACCESS_EXPIRE_MINUTES`
- `JWT_REFRESH_EXPIRE_DAYS`
- `CORS_ORIGINS`
- `PORTAL_WEB_URL`
- `ADMIN_WEB_URL`
- `API_BASE_URL`

### 2.5 本地开发启动顺序
固定流程：

1. 确认本机 `postgresql@16` 已启动
2. 运行 `infra/scripts/local-infra.sh up` 检查连接并自动建库
3. 启动 API：运行 migration + seed
4. 启动 `admin-web`
5. 启动 `portal-web`

## 3. 数据库总设计

### 3.1 数据库策略
- 正式数据库唯一方案：`PostgreSQL 16`
- 所有业务主键使用 `uuid`
- 所有时间使用 `timestamptz`
- 所有状态字段使用 `text + check constraint`
- 所有写模型必须落表，不做纯缓存状态
- 所有统计字段使用“日志表 + 冗余累计值”
- 所有 migration 通过 Alembic 管理

### 3.2 必装扩展
```sql
create extension if not exists "pgcrypto";
create extension if not exists "pg_trgm";
```

### 3.3 核心实体关系
- `users` 与 `roles` 多对多，通过 `user_roles`
- `skills` 属于一个 `category`
- `skills` 与 `tags` 多对多，通过 `skill_tags`
- `skills` 拥有多个 `skill_versions`
- `skill_versions` 绑定 `file_assets`
- `skill_versions` 拥有多条 `version_reviews`
- `favorites` 关联 `users` 与 `skills`
- `download_logs` 关联 `skills`、`skill_versions`、`users`
- `audit_logs` 记录后台写操作
- `refresh_tokens` 记录登录刷新令牌

### 3.4 表结构 SQL

#### roles
```sql
create table roles (
  id uuid primary key default gen_random_uuid(),
  code text not null,
  name text not null,
  created_at timestamptz not null default now(),
  constraint uq_roles_code unique (code),
  constraint ck_roles_code check (code in ('viewer','contributor','reviewer','publisher','admin'))
);
```

#### users
```sql
create table users (
  id uuid primary key default gen_random_uuid(),
  username text not null,
  password_hash text not null,
  display_name text not null,
  email text,
  status text not null default 'active',
  last_login_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint uq_users_username unique (username),
  constraint uq_users_email unique (email),
  constraint ck_users_status check (status in ('active','disabled'))
);
```

#### user_roles
```sql
create table user_roles (
  user_id uuid not null,
  role_id uuid not null,
  created_at timestamptz not null default now(),
  primary key (user_id, role_id),
  constraint fk_user_roles_user foreign key (user_id) references users(id) on delete cascade,
  constraint fk_user_roles_role foreign key (role_id) references roles(id) on delete cascade
);
```

#### categories
```sql
create table categories (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  slug text not null,
  icon text,
  description text,
  sort_order integer not null default 0,
  is_visible boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint uq_categories_slug unique (slug),
  constraint uq_categories_name unique (name)
);
```

#### tags
```sql
create table tags (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  slug text not null,
  created_at timestamptz not null default now(),
  constraint uq_tags_slug unique (slug),
  constraint uq_tags_name unique (name)
);
```

#### file_assets
```sql
create table file_assets (
  id uuid primary key default gen_random_uuid(),
  bucket text not null,
  object_key text not null,
  original_name text not null,
  mime_type text not null,
  size_bytes bigint not null,
  sha256 text not null,
  file_kind text not null,
  created_by uuid,
  created_at timestamptz not null default now(),
  constraint uq_file_assets_object unique (bucket, object_key),
  constraint uq_file_assets_sha256_kind unique (sha256, file_kind),
  constraint fk_file_assets_created_by foreign key (created_by) references users(id),
  constraint ck_file_assets_kind check (file_kind in ('package','readme','icon','screenshot','attachment'))
);
```

#### skills
```sql
create table skills (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  slug text not null,
  summary text not null,
  description text not null,
  owner_user_id uuid not null,
  category_id uuid not null,
  icon_file_id uuid,
  status text not null default 'active',
  current_published_version_id uuid,
  latest_version_no text,
  view_count bigint not null default 0,
  download_count bigint not null default 0,
  favorite_count bigint not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  published_at timestamptz,
  constraint uq_skills_slug unique (slug),
  constraint fk_skills_owner foreign key (owner_user_id) references users(id),
  constraint fk_skills_category foreign key (category_id) references categories(id),
  constraint fk_skills_icon foreign key (icon_file_id) references file_assets(id),
  constraint ck_skills_status check (status in ('active','inactive'))
);
```

#### skill_tags
```sql
create table skill_tags (
  skill_id uuid not null,
  tag_id uuid not null,
  created_at timestamptz not null default now(),
  primary key (skill_id, tag_id),
  constraint fk_skill_tags_skill foreign key (skill_id) references skills(id) on delete cascade,
  constraint fk_skill_tags_tag foreign key (tag_id) references tags(id) on delete cascade
);
```

#### skill_versions
```sql
create table skill_versions (
  id uuid primary key default gen_random_uuid(),
  skill_id uuid not null,
  version text not null,
  manifest_json jsonb not null,
  changelog text not null default '',
  install_notes text not null default '',
  breaking_changes text not null default '',
  readme_markdown text not null,
  source_type text not null default 'upload_zip',
  package_file_id uuid not null,
  readme_file_id uuid,
  review_status text not null default 'draft',
  review_comment text,
  reviewed_by uuid,
  reviewed_at timestamptz,
  published_by uuid,
  published_at timestamptz,
  created_by uuid not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint uq_skill_versions_skill_version unique (skill_id, version),
  constraint fk_skill_versions_skill foreign key (skill_id) references skills(id) on delete cascade,
  constraint fk_skill_versions_package foreign key (package_file_id) references file_assets(id),
  constraint fk_skill_versions_readme foreign key (readme_file_id) references file_assets(id),
  constraint fk_skill_versions_reviewed_by foreign key (reviewed_by) references users(id),
  constraint fk_skill_versions_published_by foreign key (published_by) references users(id),
  constraint fk_skill_versions_created_by foreign key (created_by) references users(id),
  constraint ck_skill_versions_status check (review_status in ('draft','submitted','approved','rejected','published','archived')),
  constraint ck_skill_versions_source check (source_type = 'upload_zip')
);
```

#### version_reviews
```sql
create table version_reviews (
  id uuid primary key default gen_random_uuid(),
  skill_version_id uuid not null,
  action text not null,
  comment text not null default '',
  operator_user_id uuid not null,
  created_at timestamptz not null default now(),
  constraint fk_version_reviews_version foreign key (skill_version_id) references skill_versions(id) on delete cascade,
  constraint fk_version_reviews_operator foreign key (operator_user_id) references users(id),
  constraint ck_version_reviews_action check (action in ('submit','approve','reject','publish','archive','rollback_publish'))
);
```

#### favorites
```sql
create table favorites (
  user_id uuid not null,
  skill_id uuid not null,
  created_at timestamptz not null default now(),
  primary key (user_id, skill_id),
  constraint fk_favorites_user foreign key (user_id) references users(id) on delete cascade,
  constraint fk_favorites_skill foreign key (skill_id) references skills(id) on delete cascade
);
```

#### download_logs
```sql
create table download_logs (
  id uuid primary key default gen_random_uuid(),
  skill_id uuid not null,
  skill_version_id uuid not null,
  user_id uuid,
  ip inet,
  user_agent text,
  created_at timestamptz not null default now(),
  constraint fk_download_logs_skill foreign key (skill_id) references skills(id),
  constraint fk_download_logs_version foreign key (skill_version_id) references skill_versions(id),
  constraint fk_download_logs_user foreign key (user_id) references users(id)
);
```

#### audit_logs
```sql
create table audit_logs (
  id uuid primary key default gen_random_uuid(),
  actor_user_id uuid,
  action text not null,
  target_type text not null,
  target_id uuid,
  before_json jsonb,
  after_json jsonb,
  created_at timestamptz not null default now(),
  constraint fk_audit_logs_actor foreign key (actor_user_id) references users(id)
);
```

#### refresh_tokens
```sql
create table refresh_tokens (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null,
  token_hash text not null,
  expires_at timestamptz not null,
  revoked_at timestamptz,
  created_at timestamptz not null default now(),
  constraint fk_refresh_tokens_user foreign key (user_id) references users(id) on delete cascade,
  constraint uq_refresh_tokens_hash unique (token_hash)
);
```

### 3.5 索引
```sql
create index idx_categories_visible_sort on categories(is_visible, sort_order);
create index idx_skills_category_status on skills(category_id, status);
create index idx_skills_published_at on skills(published_at desc);
create index idx_skills_download_count on skills(download_count desc);
create index idx_skills_favorite_count on skills(favorite_count desc);
create index idx_skills_name_trgm on skills using gin (name gin_trgm_ops);
create index idx_skills_summary_trgm on skills using gin (summary gin_trgm_ops);
create index idx_skill_versions_skill_status on skill_versions(skill_id, review_status);
create index idx_skill_versions_published_at on skill_versions(published_at desc);
create index idx_version_reviews_version_created on version_reviews(skill_version_id, created_at desc);
create index idx_download_logs_skill_created on download_logs(skill_id, created_at desc);
create index idx_audit_logs_target on audit_logs(target_type, target_id, created_at desc);
create unique index uq_skill_versions_one_published
on skill_versions(skill_id)
where review_status = 'published';
```

### 3.6 触发器与函数
```sql
create or replace function set_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

create trigger trg_users_updated_at
before update on users
for each row execute function set_updated_at();

create trigger trg_categories_updated_at
before update on categories
for each row execute function set_updated_at();

create trigger trg_skills_updated_at
before update on skills
for each row execute function set_updated_at();

create trigger trg_skill_versions_updated_at
before update on skill_versions
for each row execute function set_updated_at();
```

### 3.7 数据库级规则
- 同一 skill 只能有一个 `published` 版本，由部分唯一索引强制保证。
- `skills.slug` 全局唯一。
- `categories` 被 skill 引用时禁止删除。
- `favorites` 通过联合主键天然去重。
- 所有带 `updated_at` 的表统一由触发器自动刷新。
- 所有写操作必须在应用层额外记录 `audit_logs`。

### 3.8 初始化数据
初始化 migration 或 seed 脚本必须插入：

- 默认角色：
  - `viewer`
  - `contributor`
  - `reviewer`
  - `publisher`
  - `admin`
- 默认管理员账号：
  - `username=admin`
  - `password=ChangeMe123!`
  - 首次登录后强制建议修改
- 初始分类：
  - `ai-intelligence`
  - `developer-tools`
  - `productivity`
  - `data-analysis`
  - `content-creation`
  - `security-compliance`
  - `communication-collaboration`

### 3.9 Migration 计划
- `0001_enable_extensions`
  - 安装 `pgcrypto` 与 `pg_trgm`
- `0002_create_auth_tables`
  - `roles`、`users`、`user_roles`、`refresh_tokens`
- `0003_create_taxonomy_tables`
  - `categories`、`tags`
- `0004_create_file_assets`
  - `file_assets`
- `0005_create_skill_tables`
  - `skills`、`skill_tags`
- `0006_create_skill_versions`
  - `skill_versions`
- `0007_create_reviews_and_logs`
  - `version_reviews`、`favorites`、`download_logs`、`audit_logs`
- `0008_create_indexes_and_triggers`
  - 所有索引、唯一索引、`updated_at` 触发器
- `0009_seed_initial_data`
  - 默认角色、管理员、默认分类

## 4. 后端实施规格

### 4.1 模块边界
- `auth`
  - 登录
  - 刷新 token
  - 退出登录
  - 当前用户
- `users`
  - 用户查询
  - 创建用户
  - 禁用/启用
  - 角色分配
- `categories`
  - 后台分类 CRUD
  - 前台分类查询
- `skills`
  - 技能主档查询/编辑
  - 技能列表查询
- `versions`
  - 上传
  - 版本详情
  - 编辑 draft/rejected 元数据
  - 状态流转
- `reviews`
  - 审核列表
  - 审核动作
- `favorites`
  - 收藏/取消收藏
- `downloads`
  - 下载记录
  - 预签名 URL
- `audit`
  - 审计日志查询
- `files`
  - 对象存储上传
  - 文件元数据入库

### 4.2 上传包规范
- 仅支持 `.zip`
- 最大文件大小：`50MB`
- ZIP 根目录必须包含：
  - `skill.yaml`
  - `README.md`
- 可选文件：
  - `icon.png`
  - `icon.jpg`
  - `icon.svg`
  - `screenshots/*`
  - `assets/*`
  - `LICENSE`

`skill.yaml` 字段固定为：

```yaml
name: string
slug: string
version: semver
summary: string
description: string
category: string
tags:
  - string
author: string
homepage: string optional
repository: string optional
license: string optional
```

校验规则：
- `name` 长度 1-80
- `slug` 仅允许小写字母、数字、中划线
- `version` 必须为 semver
- `summary` 长度 1-160
- `description` 长度 1-5000
- `category` 必须命中数据库现有分类 slug
- `tags` 最多 10 个
- 禁止 ZIP Slip 路径穿越
- 文本文件按 UTF-8 读取

### 4.3 版本状态机
- `draft`
  - 可编辑
  - 可删除
  - 可提交审核
- `submitted`
  - 不可编辑
  - reviewer 可通过/拒绝
- `approved`
  - publisher/admin 可发布
- `rejected`
  - 可补充修改
  - 可重新提交
- `published`
  - 不可编辑
  - 可归档
  - 可被回滚替换
- `archived`
  - 不可编辑
  - 可回滚发布

非法状态流转统一返回 `409 Conflict`。

### 4.4 API 一览

#### 认证
- `POST /api/auth/login`
- `POST /api/auth/refresh`
- `POST /api/auth/logout`
- `GET /api/auth/me`

#### 前台公共接口
- `GET /api/public/categories`
- `GET /api/public/skills`
  - 查询参数：
    - `category`
    - `tag`
    - `q`
    - `sort`
    - `page`
    - `page_size`
- `GET /api/public/skills/{slug}`
- `POST /api/public/skills/{id}/favorite`
- `DELETE /api/public/skills/{id}/favorite`
- `GET /api/public/skills/{id}/download`

#### 后台接口
- `POST /api/admin/skills/upload`
- `GET /api/admin/skills`
- `GET /api/admin/skills/{id}`
- `PATCH /api/admin/skills/{id}`
- `GET /api/admin/skills/{id}/versions`
- `GET /api/admin/versions/{id}`
- `PATCH /api/admin/versions/{id}`
- `POST /api/admin/versions/{id}/submit`
- `POST /api/admin/versions/{id}/approve`
- `POST /api/admin/versions/{id}/reject`
- `POST /api/admin/versions/{id}/publish`
- `POST /api/admin/versions/{id}/archive`
- `POST /api/admin/versions/{id}/rollback`
- `GET /api/admin/reviews`
- `GET /api/admin/categories`
- `POST /api/admin/categories`
- `PATCH /api/admin/categories/{id}`
- `DELETE /api/admin/categories/{id}`
- `GET /api/admin/users`
- `POST /api/admin/users`
- `PATCH /api/admin/users/{id}`
- `POST /api/admin/users/{id}/roles`
- `POST /api/admin/users/{id}/disable`
- `POST /api/admin/users/{id}/enable`
- `GET /api/admin/audit-logs`

统一响应格式：

```json
{
  "code": 0,
  "message": "ok",
  "data": {}
}
```

### 4.5 鉴权规则
- `viewer`
  - 仅前台浏览
- `contributor`
  - 上传
  - 编辑 draft/rejected
  - 提交审核
- `reviewer`
  - 审核通过/拒绝
- `publisher`
  - 发布/归档/回滚
- `admin`
  - 全权限

### 4.6 事务性操作

#### 上传创建
事务内完成：
- 文件上传到对象存储
- `file_assets` 入库
- 首次上传时创建 `skills`
- 创建 `skill_versions`
- 写 `audit_logs`

#### 审核通过
事务内完成：
- 更新 `skill_versions.review_status=approved`
- 写 `reviewed_by`
- 写 `reviewed_at`
- 插入 `version_reviews`
- 插入 `audit_logs`

#### 审核拒绝
事务内完成：
- 更新 `review_status=rejected`
- 落拒绝原因
- 插入 `version_reviews`
- 插入 `audit_logs`

#### 发布
事务内完成：
- 将旧 `published` 改 `archived`
- 新版本改 `published`
- 更新 `skills.current_published_version_id`
- 更新 `skills.latest_version_no`
- 更新 `skills.published_at`
- 插入 `version_reviews`
- 插入 `audit_logs`

#### 归档
事务内完成：
- 当前发布版本改 `archived`
- `skills.current_published_version_id` 置空
- 前台该 skill 隐藏
- 插入 `version_reviews`
- 插入 `audit_logs`

#### 回滚
事务内完成：
- 当前发布版本改 `archived`
- 指定历史版本改 `published`
- 更新 `skills.current_published_version_id`
- 更新 `skills.latest_version_no`
- 插入 `version_reviews`
- 插入 `audit_logs`

### 4.7 安全规则
- access token 使用 JWT
- refresh token 保存 hash，不保存明文
- 密码哈希使用 `argon2`
- README 渲染走安全白名单，不允许原始 HTML 注入
- 文件下载通过 MinIO/S3 预签名 URL
- 上传 ZIP 做文件名与路径穿越校验
- 后台写操作全部写审计日志
- 登录、上传、下载接口做基础限流

## 5. 前端实施规格

### 5.1 前台 portal-web

#### 路由
- `/categories`
  - 使用查询参数 `?skill=<slug>` 控制详情抽屉开合

#### 页面布局
- 顶部简导航
- 页面标题区
- 分类胶囊区
- 搜索/排序工具栏
- 技能卡片网格
- 分页区
- 详情抽屉

#### 数据来源
- 分类：`GET /api/public/categories`
- 列表：`GET /api/public/skills`
- 详情：`GET /api/public/skills/{slug}`
- 收藏：`POST/DELETE /api/public/skills/{id}/favorite`
- 下载：`GET /api/public/skills/{id}/download`

#### 卡片字段
- 图标
- 名称
- 分类
- 标签摘要
- 短描述
- 下载量
- 收藏量
- 当前版本

#### 详情抽屉字段
- 名称
- 作者
- 当前版本
- 分类
- 标签
- 摘要
- 详细描述
- README 渲染内容
- 更新日志
- 历史版本列表
- 收藏按钮
- 下载按钮
- 最近发布时间

#### 状态处理
- 首屏加载 skeleton
- 空结果空态
- 接口失败错误态
- 抽屉详情加载中态

### 5.2 后台 admin-web

#### 登录页
- 字段：
  - 用户名
  - 密码
- 动作：
  - 登录
- 错误态：
  - 凭证错误提示

#### Dashboard
- 数据来源：
  - 后续可聚合 `/api/admin/skills`、`/api/admin/reviews`
- 展示：
  - 总技能数
  - 已发布数
  - 待审核数
  - 最近发布

#### 技能列表页
- 数据来源：
  - `GET /api/admin/skills`
- 表格列：
  - 名称
  - slug
  - 分类
  - 当前发布版本
  - 状态
  - 创建人
  - 更新时间
- 按钮动作：
  - 上传技能
  - 查看详情
  - 上传新版本

#### 技能详情页
- 数据来源：
  - `GET /api/admin/skills/{id}`
  - `GET /api/admin/skills/{id}/versions`
- 展示：
  - 主档信息
  - 标签
  - 版本时间线
  - 当前发布版本

#### 版本详情页
- 数据来源：
  - `GET /api/admin/versions/{id}`
- 展示：
  - Manifest 解析结果
  - README
  - 更新日志
  - 安装说明
  - 当前状态
- 按钮动作：
  - 提交审核
  - 审核通过
  - 审核拒绝
  - 发布
  - 归档
  - 回滚

#### 审核中心
- 数据来源：
  - `GET /api/admin/reviews`
- 表格列：
  - Skill 名称
  - 版本
  - 提交人
  - 提交时间
  - 当前状态
- 动作：
  - 进入版本详情
  - 审核通过
  - 审核拒绝

#### 分类管理
- 数据来源：
  - `GET /api/admin/categories`
- 字段：
  - 名称
  - slug
  - 图标
  - 描述
  - 排序
  - 是否展示
- 动作：
  - 新建
  - 编辑
  - 删除

#### 用户管理
- 数据来源：
  - `GET /api/admin/users`
- 表格列：
  - 用户名
  - 显示名
  - 邮箱
  - 状态
  - 角色
  - 最近登录
- 动作：
  - 创建用户
  - 启用/禁用
  - 分配角色

#### 审计日志页
- 数据来源：
  - `GET /api/admin/audit-logs`
- 表格列：
  - 操作人
  - 动作
  - 目标类型
  - 目标 ID
  - 时间

### 5.3 响应式要求
- 桌面：1440 宽显示 4 列卡片
- 平板：768 宽显示 2 列卡片
- 手机：390 宽显示 1 列卡片

## 6. 任务分解与优先级

### M1 基础工程与基础设施
- [x] 初始化根目录工程结构
- [x] 创建 `apps/portal-web`
- [x] 创建 `apps/admin-web`
- [x] 创建 `apps/api-server`
- [x] 创建根目录 `.gitignore`
- [x] 创建根目录 `.env.example`
- [x] 完成本地 PostgreSQL 运行脚本
- [x] 清理 Docker/Nginx 本地开发依赖
- [x] 准备本地基础设施启动脚本

### M2 认证与权限
- [x] 在后端创建 `auth` 模块
- [x] 在后端创建 `users` 模块
- [x] 实现密码哈希与校验
- [x] 实现 JWT access token
- [x] 实现 refresh token 入库与轮换
- [x] 实现 `/api/auth/login`
- [x] 实现 `/api/auth/refresh`
- [x] 实现 `/api/auth/logout`
- [x] 实现 `/api/auth/me`
- [x] 实现后台路由守卫
- [ ] 实现后台菜单级权限控制

### M3 数据库与迁移
- [x] 初始化 Alembic
- [x] 创建 `0001_enable_extensions`
- [x] 创建 `0002_create_auth_tables`
- [x] 创建 `0003_create_taxonomy_tables`
- [x] 创建 `0004_create_file_assets`
- [x] 创建 `0005_create_skill_tables`
- [x] 创建 `0006_create_skill_versions`
- [x] 创建 `0007_create_reviews_and_logs`
- [x] 创建 `0008_create_indexes_and_triggers`
- [x] 创建 `0009_seed_initial_data`
- [x] 验证空库迁移成功

### M4 技能上传与版本域
- [x] 创建上传接口骨架
- [x] 实现 ZIP 文件大小与类型校验
- [x] 实现临时解包
- [x] 实现 ZIP Slip 防护
- [x] 实现 `skill.yaml` 解析
- [x] 实现 `README.md` 解析
- [x] 实现分类 slug 校验
- [x] 实现 semver 校验
- [x] 实现对象存储上传
- [x] 实现 `file_assets` 入库
- [x] 实现首次上传创建 `skills`
- [x] 实现后续上传创建 `skill_versions`
- [x] 实现版本详情查询
- [x] 实现 draft/rejected 元数据编辑

### M5 审核发布链路
- [x] 实现提交审核接口
- [x] 实现审核列表接口
- [x] 实现审核通过接口
- [x] 实现审核拒绝接口
- [x] 实现发布接口
- [x] 实现归档接口
- [x] 实现回滚接口
- [x] 实现 `version_reviews` 写入
- [x] 实现 `audit_logs` 写入
- [x] 验证“同 skill 仅一个 published”规则

### M6 后台页面
- [x] 初始化后台登录页
- [x] 初始化后台主布局
- [x] 实现 Dashboard 页面
- [x] 实现技能列表页
- [x] 实现技能详情页
- [x] 实现版本详情页
- [x] 实现审核中心页
- [x] 实现分类管理页
- [x] 实现用户管理页
- [x] 实现审计日志页

### M7 前台广场
- [x] 初始化前台主布局
- [x] 实现 `/categories` 路由
- [x] 实现分类胶囊筛选
- [x] 实现搜索框
- [x] 实现排序下拉
- [x] 实现卡片网格
- [x] 实现分页
- [x] 实现详情抽屉
- [x] 实现 `?skill=` 深链恢复
- [x] 实现收藏操作
- [x] 实现下载操作
- [x] 完成移动端适配

### M8 测试与部署
- [x] 编写后端单元测试基础框架
- [x] 编写上传校验测试
- [x] 编写状态流转测试
- [x] 编写权限测试
- [x] 编写前台页面基础交互测试
- [x] 编写后台页面基础交互测试
- [x] 编写本地 PostgreSQL 启动说明
- [x] 编写部署说明
- [x] 准备示例技能包数据
- [ ] 做一轮全链路验收

## 7. 进度与执行控制

### Current Stage
- 当前阶段：`企业级补全与文档体系重构`
- 当前状态：`in_progress`

### Progress Log
- 2026-03-24 20:20 CST：创建主计划文件，固化系统目标、技术栈、数据库 SQL、后端规格、前端规格、任务拆解与执行控制结构。下一步先从基础工程骨架开始。
- 2026-03-24 20:52 CST：完成第一轮骨架落地，已创建 monorepo 工作区文件、前台 portal-web 最小 Vite React 骨架、后台 admin-web 最小 Vite React 骨架、FastAPI 最小服务骨架与共享 packages 脚手架。该共享脚手架后续因未启用已清理，仅保留该条作为历史演进记录。下一步补本地基础设施启动脚本与后端 Alembic 初始化。
- 2026-03-24 21:59 CST：完成 `infra/scripts/local-infra.sh` 初版，并完成 `bash -n` 语法验证。
- 2026-03-24 23:00 CST：已在 `apps/api-server` 下完成 Alembic 工程初始化（`alembic.ini`、`alembic/env.py`、`alembic/script.py.mako`、`alembic/versions`），并创建 `0001_enable_extensions`、`0002_create_auth_tables`、`0003_create_taxonomy_tables` 迁移骨架（其中 `0001` 已写入 PostgreSQL 扩展安装语句）。同时为配置新增 `sqlalchemy_database_uri` 统一连接串。验证方面执行了 Python AST 语法检查通过。受当前环境缺少 Alembic 运行依赖与 Python 缓存目录写权限限制，未能在本沙箱执行 `alembic history/upgrade` 的运行时验证。
- 2026-03-25 00:05 CST：已从项目内移除旧的自动推进残留，包括 `infra/scripts/skill-hub-continuation-worker.sh`、自动提示词文档与 `.runtime/skill-hub-worker` 运行文件，并将 `.runtime/` 加入忽略列表。后续项目推进不再依赖定时 worker，只保留本计划文件作为人工与 Codex 的接力控制面。
- 2026-03-25 00:18 CST：后端工程已切换为 `.venv` 约定，并新增 `infra/scripts/setup-api-venv.sh` 用于创建虚拟环境和安装开发依赖。
- 2026-03-25 00:28 CST：根据本机实际环境将后端 Python 版本约束从 `3.13` 调整为 `3.14`，已同步更新 `apps/api-server/.python-version`、`pyproject.toml`、`README.md` 和 `.venv` 初始化脚本。下一步直接使用本机 `python3.14` 初始化 `apps/api-server/.venv` 并执行 migration / API 运行验证。
- 2026-03-25 00:41 CST：项目本地运行方式切换完成，已删除 `infra/docker/docker-compose.yml` 与 `infra/nginx/default.conf`，并将 `infra/scripts/local-infra.sh` 重写为基于本机 PostgreSQL 服务的本地数据库检查/建库脚本。后续开发与验证不再依赖 Docker。
- 2026-03-25 00:52 CST：已基于本机 Homebrew `postgresql@16` 完成本地运行链路验证，`apps/api-server/.venv` 使用 Python 3.14 创建成功，`alembic upgrade head` 已执行通过，且通过 `TestClient` 验证了 `/api/auth/login`、`/api/auth/me`、`/api/public/categories`、`/api/admin/categories`、`/api/admin/skills` 与 `/api/auth/logout`。当前项目本地运行不再依赖 Docker。
- 2026-03-25 01:01 CST：数据库配置风格已向 EIBM 项目对齐，后端改为以 `DATABASE_URL` / `TEST_DATABASE_URL` 为主的单连接串模式，新增 `app/core/database.py` 统一承载 `engine`、`SessionLocal` 与 `get_db`，Alembic 直接读取 `settings.database_url`，并补充了参考 EIBM 的 `tests/conftest.py` 自动建测试库入口。
- 2026-03-25 01:45 CST：完成“真实技能列表”只读闭环的主体实现，新增 `/api/public/skills` 与分页版 `/api/admin/skills`，抽出技能列表 repository/service，补充本地样例技能 seed 脚本，并将后台拆成真实技能列表页、前台改为真实技能卡片网格与分页渲染。当前阶段不含详情抽屉、上传 ZIP 与审核发布。
- 2026-03-25 02:05 CST：完成本阶段本地验证，当时使用测试演示数据写入 6 个样例技能（4 个已发布）来跑通技能列表与权限回归；后续已将这类演示数据迁移为测试专用 seed，不再作为运行时默认开发方式。后端 `pytest` 通过 4 个技能列表与权限测试，`admin-web` 与 `portal-web` 均已通过生产构建。当前剩余高优先级能力是技能详情抽屉与后台技能详情页。
- 2026-03-25 03:30 CST：完成 Skill Hub 内测闭环主体实现，后端已补齐技能详情、版本详情、上传 ZIP、提审、审核、发布、归档、回滚、收藏、下载、审计与只读后台管理接口；前台已接入详情抽屉、`?skill=` 深链、登录后收藏、技能包下载；后台已接入技能详情页、版本详情页、审核中心与只读分类/用户/审计页。验证方面，后端 `pytest` 共 11 项全部通过，前后台生产构建均通过，样例技能 seed 可正常落本地文件与数据库。
- 2026-03-25 10:55 CST：完成生产化第一轮落地，后端新增 `APP_ENV/STORAGE_BACKEND/LOG_FORMAT` 配置分层、请求 ID 中间件、结构化 JSON 日志、统一异常响应、`/health/live` 与 `/health/ready`、Redis 限流、S3/本地双存储抽象、审计 `request_id` 字段、分类 CRUD、用户角色分配与启停用、审计日志过滤与 CSV 导出，并补齐 `systemd`、`nginx`、`release-check.sh` 与部署/回滚/备份文档。前端已将分类/用户/审计页升级为可运营页面，并补充了移动端样式与 Playwright 冒烟脚本。验证方面，后端 `pytest` 已扩展到 15 项全部通过，前后台生产构建通过；Playwright 测试文件与运行链路已接通，但 CLI 在当前桌面环境中仍存在挂起，需要继续做一次稳定的全链路冒烟。
- 2026-03-25 12:40 CST：完成前台门户体验收口，首页已改为“技能广场优先、平台概览后置”，分类探索与技能列表合并为统一的技能广场区域，并按腾讯 SkillHub 分类区提取的同款图标形态与配色重做分类卡片；同时统一了前台主按钮、上传弹窗、Logo 文案区和详情抽屉操作按钮样式。后端同步修复可选登录态依赖，公开技能详情在本地残留无效 token 时不再返回 `401`，前台 `?skill=` 详情抽屉已重新验证可正常打开。验证方面，后端 `pytest tests/test_skill_workflow.py` 9 项通过，`portal-web` 生产构建通过，并完成了一轮本地浏览器冒烟。
- 2026-03-25 13:44 CST：完成技能详情增强与点赞能力落地，数据库新增 `skills.like_count`、`skill_likes` 与 `skill_versions.usage_guide_json`，后端详情接口已返回 `is_liked + usage_guide`，并新增点赞/取消点赞接口；上传与样例 seed 会自动生成 Agent/Human 两套默认使用指引。前台详情抽屉已升级为包含“我是 Agent / 我是 Human”双 Tab、复制按钮和点赞/收藏/下载三套独立交互，后台版本详情页也已支持编辑版本级使用方式配置。验证方面，后端 `pytest tests/test_skill_workflow.py` 10 项通过，前后台生产构建通过，本地数据库已执行 `alembic upgrade head` 并完成样例数据重置，公开详情接口已确认返回点赞统计和完整使用指引。
- 2026-03-25 16:12 CST：完成 Skill 详情页独立路由化与后台自定义角色权限体系落地。前台技能详情已从抽屉切换为 `/skills/:slug` 独立详情页，保留点赞、收藏、下载、Agent/Human 使用指引、README 和历史版本，并支持从详情返回技能广场时恢复原筛选状态。后端新增 `permissions`、`role_permissions` 及 `roles.description/is_system/is_active`，默认角色已映射到权限点，后台所有核心接口改为按权限点鉴权；同时新增角色管理接口与后台角色管理页，用户管理页也已改成从真实角色列表分配角色。验证方面，本地数据库已执行 `alembic upgrade head` 到 `0012_custom_roles_perms`，后端 `pytest` 共 20 项通过，前后台生产构建通过，并补充了“自定义角色 + 权限点”回归测试。
- 2026-03-25 18:35 CST：完成企业级补全第一轮落地。项目根目录已新增 `AGENTS.md`，并在 `docs/` 下按 `00-overview / 10-architecture / 20-engineering / 30-product-flows / 40-runbooks / 50-prompts` 拆分长期维护文档，工程提示词不再依赖单文件。后台新增“待发布”和“处理记录”工作台，技能列表补齐线上版本、最新版本状态、待审核/待发布数量与互动统计，技能详情补齐授权对象、点赞/收藏/下载统计与明细，以及 skill 级授权的角色/指定人配置。后端补齐 `skill_role_grants`、`skill_user_grants`、待发布/历史/skill 统计与权限接口，并扩展样例 seed 为待审核、待发布、已拒绝等完整演示数据。验证方面，全量后端 `pytest` 23 项通过，`admin-web` 与 `portal-web` 生产构建通过。
- 2026-03-25 19:10 CST：完成文档体系细化升级。已重写根级 `AGENTS.md`，并把 `docs/10-architecture`、`docs/20-engineering`、`docs/30-product-flows`、`docs/40-runbooks`、`docs/50-prompts` 下核心文档从“原则提纲”补成“可执行规范”；新增 `repository-structure`、`doc-update-matrix`、`code-review-guide`、`admin-workbench` 以及 `docs/deploy/README.md`，同时扩写 `00-overview` 层的项目地图和产品边界。当前文档已能明确回答权限判定、审核待发布路径、仓库结构落点、统计口径、测试阻断项和 AI/人工协作入口。

### Next Task
- 完成 Playwright 全链路冒烟与生产环境 smoke checklist，重点验证审核中心、待发布、处理记录、skill 授权配置与统计数据面，再处理前后端 chunk 过大警告、S3/Redis 真实联调和 `.env.production` 模板化交付。
