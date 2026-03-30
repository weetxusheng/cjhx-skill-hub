# 领域模块图与模块边界

> **OWNER**: Skill Hub 技术负责人
>
> **Last reviewed**: 2026-03-28
>
> **Change triggers**: 仓库结构 / 模块划分 / 跨层调用规则 / 新增业务域 / 页面结构

## Purpose
本文件定义 Skill Hub 的领域模块划分、目录落点和跨层调用边界，解决“新功能知道做什么，但不知道放哪里、拆到哪一层”的问题。

## Scope
- 覆盖：
  - `apps/portal-web`
  - `apps/admin-web`
  - `apps/api-server`
  - 与业务实现直接相关的目录职责
- 不覆盖：
  - 视觉样式细则
  - 单个 API 字段定义
  - 部署脚本与运维运行细节

## Canonical Domain Map
当前 Skill Hub 统一按以下业务域组织实现：

| 领域 | 核心职责 | 主要对象 |
|---|---|---|
| `auth` | 登录、刷新、登出、会话恢复 | user, role, permission, refresh token |
| `skills` | skill 主档、公开列表、详情、展示信息编辑 | skill, category, tag |
| `versions` | skill 版本、README、usage guide、上传后的版本文案编辑 | skill_version, file_asset |
| `reviews` | 提审、审核、拒绝、审核记录 | version_review |
| `releases` | 待发布、发布、归档、回滚 | current published version |
| `grants` | skill 级授权、owner/maintainer/reviewer/publisher/viewer | skill_role_grant, skill_user_grant |
| `stats` | 点赞、收藏、下载、趋势、运营数据面 | favorite, skill_like, download_log |
| `governance` | 分类、用户、角色、权限、审计日志 | category, role, permission, audit_log |

## Frontend Module Boundaries
### `portal-web`
- `src/pages`
  - 页面容器，只做页面级 query state、路由参数、区块编排
- `src/pages/**/_components`
  - 页面私有区块；当某个区块只服务单页时，优先放在这里
- `src/components`
  - 跨页面复用组件，例如：
    - 技能卡片
    - 详情抽屉区块
    - 上传弹窗
    - 统计卡片
- `src/lib`
  - API client、能力判定、纯工具函数、数据格式化
- `src/store`
  - 只放跨页面共享且与路由无强耦合的状态

### `admin-web`
- `src/pages/workbench`
  - 审核中心、待发布、处理记录、Dashboard 等工作台页面
- `src/pages/detail`
  - skill 详情、版本详情这类高信息密度详情页
- `src/pages/governance`
  - 分类、角色、用户、审计等治理页
- `src/pages/auth`
  - 登录、会话恢复
- `src/components`
  - 可复用业务组件；禁止直接承载整页路由逻辑
- `src/lib`
  - API client、权限与 capability 消费、查询参数工具

## Frontend File Placement Rules
### 页面、区块、组件放置决策
1. 若 UI 需要独立路由：放 `src/pages/**`
2. 若只属于单个页面区块：放该页面目录下 `_components`
3. 若被两个及以上页面复用：提升到 `src/components`
4. 若只包含数据整形、无 JSX：放 `src/lib`
5. 若需要跨页面共享但与业务视图弱相关：再评估是否进入 `src/store`

### 什么时候必须抽 `hook`
- 同一页面出现 2 组以上 query/filter/form 状态联动
- 区块内部复用到第二处
- 组件超过推荐阈值，且主要复杂度来自数据获取或派生状态

### 什么时候禁止抽“通用组件”
- 仅一页使用，且抽出后会把页面专有状态机暴露到共享层
- 视觉相似但交互语义不同
- 组件通用化后需要大量布尔 props 才能工作

## Backend Module Boundaries
### Route / Service / Repository / Schema / Model
| 层 | 允许做什么 | 禁止做什么 |
|---|---|---|
| route | 参数解析、依赖注入、轻量错误映射 | 复杂事务、跨域 SQL、缓存处理 |
| service | 状态机、事务、审计、缓存失效、写模型编排 | 页面展示拼装、数据库查询细节堆叠 |
| repository | 复杂读取、聚合列表、详情摘要查询 | 权限副作用、状态流转、审计写入 |
| schema | 入参/出参契约、DTO | 埋业务逻辑 |
| model | ORM 映射、字段定义 | 业务决策、权限判断 |

### 目录落点规则
- `app/api/routes`
  - 按能力域拆分，例如：`admin_skills.py`、`admin_reviews.py`、`public_skills.py`
- `app/services`
  - 一个文件一个核心域，禁止“万能 service”
- `app/repositories`
  - 一个文件一个查询域；若读模型明显跨域，需明确谁是主语
- `app/schemas`
  - `auth.py`、`skills.py`、`versions.py`、`governance.py` 这类按领域分组

## Backend Domain Ownership Rules
### `skills` 域
- 负责主档读写、公开展示信息、列表/详情聚合
- 可以依赖 `stats` 的聚合结果，但不应内嵌统计明细查询细节

### `versions` 域
- 负责版本读取、README/usage guide/manifest 文案编辑
- 上传后的版本编辑、版本详情聚合均以该域为主

### `reviews` 域
- 只负责 `draft -> submitted -> approved/rejected`
- 审核动作和审核记录由该域主导

### `releases` 域
- 只负责 `approved -> published -> archived -> rollback`
- 任何“当前线上版本”切换都必须由该域收口

### `grants` 域
- 负责 skill 级授权判断与授权变更
- 不负责全局角色权限聚合本身；全局角色权限仍归 `auth/governance`

### `stats` 域
- 负责点赞、收藏、下载写明细与聚合视图
- 不允许业务域各自维护一套统计口径

## Cross-Domain Call Rules
### 允许
- service 组合多个 repository
- `reviews` service 调用 `versions` repository 读取版本详情
- `releases` service 调用 `skills` repository 更新主档冗余字段
- `skills` service 调用 `grants` service 计算 capability / scope 结果

### 禁止
- route 直接跨域查 repository 拼业务
- repository 反向调用 service
- 一个 service 文件同时承载 `reviews + releases + grants + stats` 四类行为
- 前端直接根据状态码和角色名本地拼业务状态机，绕过后端 capability

## Query Ownership Rules
### 列表查询
- 列表由“列表主语”域负责
- 若页面主语是 skill，则列表 route/repository 归 `skills`
- 若页面主语是待审核版本，则列表 route/repository 归 `reviews`
- 若页面主语是待发布版本，则列表 route/repository 归 `releases`

### 详情查询
- 主档详情以 `skills` 为主
- 版本详情以 `versions` 为主
- 页面需要的 capability、最新审核记录、统计摘要可作为详情附带字段返回

### 什么时候拆独立 stats 查询
- 列表页只需汇总字段，随主列表一次返回
- 详情页需要趋势、明细、脱敏视图时，拆独立 stats 接口
- 任何包含大 JSON、长 README、长 changelog 的内容禁止混入列表接口

## New Module vs Extend Existing
### 应扩已有模块
- 只是给现有 skill 列表补筛选字段
- 给版本详情增加 usage guide 展示
- 给审核中心列表增加摘要字段

### 应新建模块或子域
- 同一文件已经同时承担“主档、版本、审核、发布”多个动作
- 新能力拥有独立状态机或权限模型
- 新页面群形成独立导航与数据主语

## Anti-Patterns
- 详情页 JSX、权限判断、查询状态、表单状态全部堆在单文件
- service 方法靠 `action` 参数分支一口气处理提审、审核、发布、回滚
- 把“能否显示按钮”逻辑散落在前端多个页面局部判断
- 列表接口为图省事返回整对象 JSON，让前端自己猜字段

## Verification
- [ ] 新增页面时，可明确判断放 `pages`、`_components`、`components` 还是 `lib`
- [ ] 新增接口时，可明确判断归属 `skills`、`versions`、`reviews`、`releases`、`grants`、`stats` 哪个域
- [ ] route/service/repository 三层职责边界清晰，不再靠工程师个人习惯决定
- [ ] 能从本文件回答“什么时候扩现有模块、什么时候新建模块”
