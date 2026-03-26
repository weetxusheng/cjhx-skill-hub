# Skill Hub 回滚指南

## 应用回滚
1. 保留最近两个前端构建产物目录，例如 `dist-release-20260325`。
2. 回滚时切换 Nginx 指向上一版静态产物，随后 `systemctl reload nginx`。
3. API 回滚时切回上一版代码目录，并重启 `skill-hub-api.service`。

## 数据库回滚
1. 先确认是否存在破坏性 migration。
2. 如需回滚最近一步 migration：
   - `cd apps/api-server`
   - `source .venv/bin/activate`
   - `alembic downgrade -1`
3. 如涉及数据变更，优先恢复备份而不是连续 downgrade 多步。

## 文件回滚
- 若启用 MinIO/S3 版本化，优先恢复对象旧版本。
- 若使用保留策略，则按对象 key 定位并恢复上一版本。

## 回滚后核验
- `GET /health/live`
- `GET /health/ready`
- 后台登录、技能列表、技能详情
- 前台 `/categories`、技能详情抽屉、下载入口
