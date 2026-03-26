# 仓库结构规范

## 根目录职责
- `apps/portal-web`：用户端技能广场
- `apps/admin-web`：后台运营与治理
- `apps/api-server`：后端服务
- `docs`：正式文档
- `infra`：脚本、部署与运行支持
- 不再保留空的 `packages/ui`、`packages/types` 脚手架；只有出现真实共享代码时才重新引入共享包目录

## `portal-web` 结构要求
- `src/pages`：页面级组件
- `src/components`：可复用组件
- `src/lib`：API、工具函数
- `src/store`：本地状态存储
- 禁止把后端业务规则硬编码在页面里

## `admin-web` 结构要求
- `src/pages`：工作台与治理页面
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

## 禁止事项
- 不要把业务逻辑塞进 CSS 或全局样式文件
- 不要把复杂查询直接写在 route
- 不要把正式规范写回 `skill-hub-master-plan.md`
