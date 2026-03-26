# 发布与恢复手册

## 与 `docs/deploy/` 的边界
- 本文件：发布顺序、检查项、回滚策略和业务 smoke
- `docs/deploy/`：更偏基础设施、环境配置和故障排查细节

## 发布前 Checklist
- `infra/scripts/release-check.sh`
- `alembic upgrade head`
- 后端全量测试通过
- 前后端构建通过
- seed 可正常导入
- 审核中心、待发布、处理记录页可打开
- skill 详情授权与统计接口可打开
- portal 详情抽屉可打开
- 仓库内没有 `.DS_Store`、`dist/`、`*.tsbuildinfo`、`test-results/`

## 发布步骤
1. 构建前端产物
2. 更新 API 代码与依赖
3. 执行 migration
4. 重启 systemd 服务
5. 执行 smoke check

## Smoke Check
- 管理员可登录后台
- 技能列表正常打开
- 审核中心展示待审核版本
- 待发布展示已通过未发布版本
- 处理记录展示最近动作
- 某个 skill 的授权对象与统计能打开
- portal 能打开详情并下载

## 回滚步骤
### 应用层回滚
- 若只是错误发布了版本，优先用后台 rollback 恢复线上版本

### 系统层回滚
1. 回滚应用代码
2. 必要时回滚 migration
3. 按 `docs/deploy/rollback.md` 恢复服务

## 恢复重点
- 数据库：按 `docs/deploy/backup-restore.md`
- 对象存储：按 bucket 版本化或备份恢复
- 若发布后出现线上版本错误，可优先通过后台 rollback 恢复业务可见状态
