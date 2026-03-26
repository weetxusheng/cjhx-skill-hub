# API Server

FastAPI backend for the Skill Hub project.

## Python Environment

- Python version: `3.14`
- Virtual environment: `apps/api-server/.venv`

Bootstrap locally:

```bash
../../infra/scripts/setup-api-venv.sh
source .venv/bin/activate
../../infra/scripts/local-infra.sh up
alembic upgrade head
uvicorn app.main:app --reload
```

## Local Runtime

- PostgreSQL: local Homebrew service `postgresql@16`
- Connection defaults come from `DATABASE_URL` / `TEST_DATABASE_URL` in the project root `.env` or `.env.example`
- No Docker or Nginx is required for local development
- 本地开发默认直接使用数据库当前真实数据；测试场景数据仅在自动化测试过程中按需动态创建，不通过仓库内预置 demo 数据集注入

如需快速生成一套可手工联调的真实数据库记录，可执行：

```bash
pnpm seed:local-workbench
```

该命令会直接向本地 PostgreSQL 写入一组用于联调的真实 skill、version、审批记录、授权、点赞/收藏/下载数据，覆盖状态包括：

- `draft`
- `submitted`
- `approved`
- `published`
- `rejected`
- `archived`

页面仍然只读取数据库当前真实状态，不会注入前端假数据。

## Current API Coverage

当前已经接通：

- 认证：`/api/auth/login` `/api/auth/refresh` `/api/auth/logout` `/api/auth/me`
- 前台：分类列表、技能列表、技能详情、收藏、下载
- 后台：技能列表、技能详情、版本详情、上传、提交审核、审核通过/拒绝、发布、归档、回滚、审核中心、只读用户/审计日志

## Validation

本地验证命令：

```bash
pytest -q
pnpm --filter admin-web build
pnpm --filter portal-web build
```
