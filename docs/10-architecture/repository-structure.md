# 仓库结构规范

## 根目录职责
- `apps/portal-web`：用户端技能广场
- `apps/admin-web`：后台运营与治理
- `apps/api-server`：后端服务
- `docs`：正式文档
- `infra`：脚本、部署与运行支持
- 不再保留空的 `packages/ui`、`packages/types` 脚手架；只有出现真实共享代码时才重新引入共享包目录

## 结构事实来源
- “目录本身放什么”以本文件为准
- “模块为何这样拆、跨层怎么调”以 `docs/10-architecture/domain-module-map.md` 为准
- “页面规格该怎么写”以 `docs/20-engineering/page-spec-template.md` 为准；其余工程实现细节统一看 `docs/20-engineering/engineering-handbook.md`

## `portal-web` 结构要求
- `src/pages`：页面级组件
- `src/pages/**/_components`：页面私有区块
- `src/components`：可复用组件
- `src/lib`：API、工具函数
- `src/store`：本地状态存储
- 禁止把后端业务规则硬编码在页面里

## `admin-web` 结构要求
- `src/pages`：工作台与治理页面
- `src/pages/workbench`：审核、待发布、处理记录、Dashboard
- `src/pages/detail`：skill 详情、版本详情
- `src/pages/governance`：用户、角色、分类、审计
- `src/pages/auth`：登录与会话恢复
- `src/components`：通用业务组件
- `src/lib`：API、权限、工具
- `src/store`：登录态和全局状态
- 新增后台页面必须先判断属于：
  - 工作台页面
  - 治理页面
  - 详情页面

## `api-server` 结构要求
- `app/api/routes`：路由
- `app/services`：业务服务
- `app/repositories`：查询
- `app/models`：模型
- `app/schemas`：输入输出
- `app/core`：基础设施

## 核心域目录建议
- `auth`：`routes/auth.py`、`services/auth.py`、`schemas/auth.py`
- `skills`：`public_skills.py` / `admin_skills.py`、`services/skills.py`、`repositories/skills.py`
- `versions`：`admin_versions.py`、版本正文/上传相关 service
- `reviews` / `releases`：按工作台动作域拆 route 与 service
- `grants`：`services/skill_access.py` 与治理/详情 capability 聚合点
- `stats`：统计明细与运营查询，必要时独立 repository/service

## 新增内容放置规则
- 新页面：
  - Portal 页 -> `apps/portal-web/src/pages`
  - Admin 页 -> `apps/admin-web/src/pages`
- 新接口：
  - 按能力域放进对应 `app/api/routes`
- 新 migration：
  - `apps/api-server/alembic/versions`
- 新测试：
  - 后端 -> `apps/api-server/tests`
  - 前端 E2E -> `tests/e2e`

## 结构决策示例
- 新增“待发布批量发布”：
  - 页面放 `apps/admin-web/src/pages/workbench`
  - 共享按钮组放 `apps/admin-web/src/components`
  - route 放 `apps/api-server/app/api/routes/admin_releases.py`
- 新增“前台详情里的趋势区块”：
  - 页面区块放 `apps/portal-web/src/pages/**/_components`
  - 若只需汇总字段，扩现有详情接口；若需要趋势/明细，再补独立 stats 接口

## 禁止事项
- 不要把业务逻辑塞进 CSS 或全局样式文件
- 不要把复杂查询直接写在 route
- 不要把正式规范写回 `skill-hub-master-plan.md`
- 不要把“目录应该怎么放”只写在 PR 描述里而不补事实来源文档
