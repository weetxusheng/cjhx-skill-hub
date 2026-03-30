# 本地开发手册

## 从零启动
1. 确认本机 PostgreSQL 可用
2. 确认 Redis 可用
3. 选择本地文件存储或 MinIO
4. 初始化后端 `.venv`
5. 执行 migration
6. 启动 API
7. 启动 admin-web
8. 启动 portal-web

## 常用命令
```bash
cd /Users/xusheng/Documents/project/cjhx-skill-hub
bash infra/scripts/local-infra.sh up
bash infra/scripts/setup-api-venv.sh
cd apps/api-server && source .venv/bin/activate
alembic upgrade head
uvicorn app.main:app --reload
```

```bash
cd /Users/xusheng/Documents/project/cjhx-skill-hub
pnpm dev:admin
pnpm dev:portal
```

### 一键启动 / 停止
如果你希望把 API、admin-web、portal-web 一起常驻拉起，并自动写入 pid / log，可直接执行：

```bash
cd /Users/xusheng/Documents/project/cjhx-skill-hub
pnpm local:start
```

`pnpm local:start` 会启动带热更新的本地开发栈：
- API 使用 `uvicorn --reload`
- admin-web / portal-web 使用 Vite dev server
- 普通代码改动不需要手工停服再启动

如果你改完代码后，只想确认项目仍然活着，或自动补拉掉线服务，执行：

```bash
cd /Users/xusheng/Documents/project/cjhx-skill-hub
pnpm local:ensure
```

停止整套本地开发栈：

```bash
cd /Users/xusheng/Documents/project/cjhx-skill-hub
pnpm local:stop
```

运行时文件默认写到：
- `.runtime/local-dev/pids/`
- `.runtime/local-dev/logs/`

默认建议：
- 开发期间不要主动执行 `pnpm local:stop`
- 普通代码改动依赖热更新；若服务意外退出，再执行 `pnpm local:ensure`
- 每次功能实现、修复、重构完成后，先执行 `pnpm local:ensure`
- 再进入手工 smoke、联调或最终测试收尾

## 数据原则
- 开发默认直接使用数据库现有数据
- 不再提供仓库内预置的 demo skill 数据脚本
- 若需要验证审核/待发布链路，请通过后台真实上传、提审、审核、发布操作生成数据

## 快速联调数据
如果你需要马上验证“技能列表 / 审核中心 / 待发布 / 处理记录 / 统计数据”这一整条闭环，可以执行：

```bash
cd /Users/xusheng/Documents/project/cjhx-skill-hub
pnpm seed:local-workbench
```

这会向本地 PostgreSQL 写入一组真实联调数据，同时生成对应的本地存储对象。默认本地对象会落到仓库根目录的 `.runtime/local-dev/storage/`，不会塞进 `apps/api-server/` 源码目录。当前覆盖：

- 已发布技能
- 待审核版本
- 已审核通过待发布版本
- 已拒绝版本
- 草稿技能
- 含归档历史的技能

默认还会创建以下联调用账号：

- `fixture_contributor / Pass123!`
- `fixture_reviewer / Pass123!`
- `fixture_publisher / Pass123!`
- `fixture_observer / Pass123!`

该命令会先清理同一批 fixture slug，再重新写入，所以可以重复执行。

## 联调顺序
1. 先执行 migration
2. 先验证 API 健康检查
3. 再打开后台
4. 最后打开前台

## 常见排查
### 后台登录后权限不对
- 清本地 localStorage
- 重新登录，确保 `/api/auth/me` 返回最新 permissions

### 审核中心没数据
- 先确认数据库里确实存在 `submitted` 和 `approved` 版本
- 如果没有，则通过后台真实操作流创建，而不是导入 demo 数据

### 前台没有技能
- 确认数据库里至少存在一个 `published` 版本

### 需要迁移到其它机器初始化数据库
- 先执行 `pnpm db:export-init-sql`
- 生成文件位于 `infra/sql/skill-hub-init.sql`
- 该文件基于“空库执行到 Alembic head”导出，包含当前 schema、索引、约束和基础 seed
- 在目标库执行示例：

```bash
/opt/homebrew/opt/postgresql@16/bin/psql -h 127.0.0.1 -U <user> -d <db_name> -f infra/sql/skill-hub-init.sql
```

## 本地推荐验证顺序
1. 技能列表
2. 审核中心
3. 待发布
4. 处理记录
5. skill 详情授权与统计
6. portal 详情抽屉
