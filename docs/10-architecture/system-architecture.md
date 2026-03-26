# 系统架构

## Runtime Topology
### 生产运行形态
- `portal-web` 与 `admin-web` 构建为静态资源，由 Nginx 托管
- `api-server` 由 systemd 管理，运行 `gunicorn + uvicorn worker`
- PostgreSQL 负责交易数据、主档、版本、权限、审计和统计明细
- Redis 负责限流、短缓存、撤销态和高频读优化
- MinIO/S3 负责 skill 包、README 文件对象和未来附件

### 本地运行形态
- 前端由 Vite dev server 启动
- API 使用 `.venv + uvicorn --reload`
- 数据库默认本机 PostgreSQL
- 存储默认走本地文件抽象，生产切换到 S3 抽象实现

## Repository Boundaries
### 根目录职责
- `apps/portal-web`：用户端技能广场
- `apps/admin-web`：后台工作台与治理页面
- `apps/api-server`：FastAPI 后端
- `docs`：正式规范、流程和运行手册
- `infra`：systemd、nginx、脚本、发布检查

### 应用边界
- `portal-web`
  - 只负责用户端发现、详情、互动和上传入口
  - 不承载后台治理逻辑
- `admin-web`
  - 承载审核、发布、权限配置、统计和治理
  - 不直接拼业务规则，依赖 API 返回的结构化数据
- `api-server`
  - 统一承载状态机、鉴权、审计、上传解析、统计聚合
  - 所有前后台业务规则以这里为最终准绳

## Backend Layering
### `app/api/routes`
- 负责路由注册、参数解析、调用 service、统一响应
- 允许：依赖注入、轻量校验、HTTP 错误映射
- 禁止：复杂 SQL、长事务编排、重复业务逻辑

### `app/services`
- 负责业务编排、状态机、事务、缓存失效、审计写入
- 允许：组合 repository、写多个模型、执行业务前后校验
- 禁止：把页面专属展示逻辑塞进 service

### `app/repositories`
- 负责复杂查询、列表聚合、工作台摘要数据
- 允许：join、子查询、mappings 输出
- 禁止：状态流转、鉴权、副作用

### `app/models`
- 负责 ORM 映射和数据库字段定义
- 禁止：复杂业务规则

### `app/schemas`
- 负责请求/响应结构
- 要求：字段名与前端消费语义保持一致

### `app/core`
- 配置、数据库、日志、中间件、限流、缓存工具

## Frontend Architecture
### `portal-web`
- 首页默认落到技能广场
- 详情以右侧抽屉为主，不打断探索链路
- 互动操作固定为点赞、收藏、下载三套独立语义
- 用户上传入口存在，但不替代后台完整工作台

### `admin-web`
- 采用工作台模型，而不是“功能页面堆叠”
- 核心运营路径：
  - 技能列表 -> 技能详情 -> 版本详情
  - 审核中心 -> 待发布 -> 处理记录
- 治理路径：
  - 分类管理
  - 用户管理
  - 角色管理
  - 审计日志

## Current Implementation State
- 用户端 skill 详情当前实现为右侧抽屉，不是独立详情页
- 后台审核流当前实现为：
  - `submitted` 进入审核中心
  - `approved` 进入待发布中心
  - `published` 才是线上版本
- skill 授权当前采用“全局权限 + skill 级授权”组合判定
- `docs/skill-hub-master-plan.md` 中早期阶段出现过独立详情页等历史记录，仅代表演进过程，不代表当前事实

## Module Relationships
### 审核发布模块
- 技能列表展示主档、线上版本、最新版本状态、待办数量
- 审核中心只处理 `submitted`
- 待发布只处理 `approved`
- 处理记录展示 `approve/reject/publish/archive/rollback`
- 版本详情是补充入口，不是唯一入口

### 授权模块
- 全局权限控制用户可见菜单和后台能力域
- skill 级授权控制单个 skill 的可操作范围
- skill 详情页是授权配置主入口

### 数据统计模块
- 明细来自 `favorites`、`skill_likes`、`download_logs`
- 汇总来自 `skills.favorite_count`、`skills.like_count`、`skills.download_count`
- skill 详情页聚合展示汇总、趋势和明细

## Infrastructure Boundaries
### PostgreSQL
- 唯一正式业务数据库
- 保存正式状态和统计明细

### Redis
- 只做缓存、限流、短期状态，不做长期事实存储

### MinIO/S3
- 负责文件对象，不负责元数据真相
- 文件元数据以数据库 `file_assets` 为准

### Nginx
- 负责静态资源和 API 反向代理
- 不承载业务规则

### systemd
- 负责 API 进程生命周期
- 与业务代码解耦

## Canonical State Flow
- Upload：创建 `draft`
- Submit：进入 `submitted`
- Approve：进入 `approved`
- Publish：进入 `published`
- Archive：进入 `archived`
- Rollback：历史版本恢复为 `published`

状态流和业务解释详见 `docs/30-product-flows/upload-review-release.md`。
