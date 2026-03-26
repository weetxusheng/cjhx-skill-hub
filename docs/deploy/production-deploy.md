# Skill Hub 生产部署

## 目标拓扑
- `Nginx` 托管 `portal-web/dist` 与 `admin-web/dist`
- `systemd` 管理 `gunicorn + uvicorn worker`
- `PostgreSQL` 提供主数据库
- `Redis` 提供限流、缓存和 refresh token 撤销辅助
- `MinIO/S3` 提供生产对象存储

## 部署步骤
1. 在目标机器准备 `python3.14`、`pnpm`、`postgresql`、`redis`、`minio` 和 `nginx`。
2. 在仓库根目录复制 `.env.example` 为 `.env.production`，至少修改：
   - `APP_ENV=production`
   - `STORAGE_BACKEND=s3`
   - `JWT_SECRET`
   - `DATABASE_URL`
   - `REDIS_URL`
   - `S3_*`
   - `ALLOWED_ORIGINS`
3. 在 `apps/api-server` 下创建并同步 `.venv` 依赖。
4. 执行 `bash infra/scripts/release-check.sh`。
5. 构建产物完成后，将 `infra/systemd/skill-hub-api.service` 安装到 `/etc/systemd/system/` 并按实际路径调整 `User`、`WorkingDirectory` 和 `EnvironmentFile`。
6. 将 `infra/nginx/skill-hub.conf` 安装到 Nginx 站点配置并按域名、证书路径调整。
7. 执行 `systemctl daemon-reload && systemctl enable --now skill-hub-api`。
8. 执行 `nginx -t && systemctl reload nginx`。
9. 验证：
   - `curl http://127.0.0.1:8000/health/live`
   - `curl http://127.0.0.1:8000/health/ready`
   - 访问 portal/admin 页面

## 发布前检查
- `.env.production` 已切到 `production`
- `JWT_SECRET` 已替换默认值
- `MinIO/S3 bucket` 已存在且可写
- `Redis` 可连接
- `alembic upgrade head` 成功
- `pnpm test:e2e` 成功
