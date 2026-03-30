# cjhx-skill-hub

创金合信技能广场（Skill Hub）——面向公司内部的技能发现、上传、审核、发布、授权与运营数据闭环平台。

## 仓库结构
- `apps/portal-web`：用户端技能广场
- `apps/admin-web`：后台运营与治理（工作台）
- `apps/api-server`：FastAPI 后端
- `docs`：正式文档（架构/流程/工程规范/运行手册）
- `infra`：本地脚本、部署与运行支持（nginx/systemd/SQL 等）
- `tests/e2e`：Playwright E2E

## 本地启动（推荐）

```bash
pnpm local:start
```

服务地址：
- API：`http://127.0.0.1:8000`
- Admin：`http://127.0.0.1:5174`
- Portal：`http://127.0.0.1:5173`

如果你只想确认本地服务仍在线（或自动补拉掉线服务）：

```bash
pnpm local:ensure
```

## 常用命令
- 管理端 build：`pnpm --filter admin-web build`
- 前台 build：`pnpm --filter portal-web build`
- E2E：`pnpm test:e2e`
- 发布级门禁：`pnpm release:check`

## 文档入口
- 项目地图：`docs/00-overview/project-map.md`
- 仓库结构规范：`docs/10-architecture/repository-structure.md`
- 工程规范导航：`docs/20-engineering/README.md`
- 本地开发手册：`docs/40-runbooks/local-development.md`
