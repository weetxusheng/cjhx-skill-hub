# 备份与恢复

## PostgreSQL 备份
- 推荐每日执行：
```bash
pg_dump "${DATABASE_URL}" --format=custom --file=/var/backups/skill-hub/skill-hub-$(date +%F).dump
```

## PostgreSQL 恢复
```bash
dropdb skill_hub
createdb skill_hub
pg_restore --clean --if-exists --no-owner --dbname="${DATABASE_URL}" /var/backups/skill-hub/skill-hub-YYYY-MM-DD.dump
```

## MinIO / S3 备份
- 开启 bucket 版本化或生命周期保留策略。
- 每日导出对象清单，并周期性同步到灾备 bucket。

## 恢复演练要求
- 每个发布周期至少执行一次数据库恢复演练
- 每个发布周期至少验证一次对象存储单文件恢复
- 演练完成后记录恢复耗时、风险点和补救动作
