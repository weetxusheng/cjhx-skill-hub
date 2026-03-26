# 故障排查

## API 无法启动
- 检查 `systemctl status skill-hub-api`
- 检查 `.env.production` 是否缺少 `JWT_SECRET`、`DATABASE_URL`、`REDIS_URL`
- 检查 `.venv` 中是否已安装 `gunicorn`

## `health/ready` 返回 503
- `database` 为 `error`：确认 PostgreSQL 可连通
- `redis` 为 `error`：确认 Redis 启动且 `REDIS_URL` 正确
- `storage` 为 `error`：确认 MinIO/S3 bucket 存在且 AK/SK 正确

## 上传后文件缺失
- 检查 `audit_logs` 是否有 `skill.upload`
- 检查对象存储 bucket 中是否存在对应 object key
- 检查 Nginx `client_max_body_size` 是否足够

## 登录大量失败
- 检查 Redis 是否可用
- 检查限流是否误伤内网出口 IP
- 查看结构化日志中的 `request_id` 关联失败请求
