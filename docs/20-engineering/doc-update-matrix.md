# 文档更新责任矩阵

## 使用方式
任何功能变更都先看“变更类型”，再按本表同步对应文档、测试和 runbook。

| 变更类型 | 必须更新的文档 | 必须检查的实现 |
|---|---|---|
| 权限模型 | `docs/10-architecture/data-and-permissions.md` `docs/30-product-flows/skill-authorization-and-metrics.md` | 鉴权、菜单、按钮、测试 |
| 状态机 / 审核流 | `docs/30-product-flows/upload-review-release.md` `docs/30-product-flows/admin-workbench.md` | service、工作台接口、测试 |
| 数据库 schema | `docs/20-engineering/database-guide.md` 对应架构文档 | migration、seed、测试 |
| API 字段 / 分页 / 错误 | `docs/20-engineering/api-and-testing.md` | route、schema、前端消费 |
| 仓库结构 | `docs/10-architecture/repository-structure.md` | 目录落点、导入边界 |
| 后台工作台 | `docs/30-product-flows/admin-workbench.md` `docs/20-engineering/frontend-guide.md` | admin 页面和 E2E |
| 统计口径 | `docs/30-product-flows/skill-authorization-and-metrics.md` | 汇总、明细、测试 |
| 测试门禁 / 回归流程 | `docs/20-engineering/api-and-testing.md` `docs/20-engineering/feature-test-playbook.md` `docs/50-prompts/qa-guide.md` `AGENTS.md` | 测试命令、Agent 执行流程、交付结论 |
| 本地开发与发布 | `docs/40-runbooks/*` 或 `docs/deploy/*` | 脚本、命令、smoke |

## 评审要求
- 评审时若发现改动命中本表但未更新文档，视为必须修复项
- 若变更跨越多个域，必须同时更新多份文档
- 若变更影响测试门禁、完成定义或 Agent 测试收尾流程，必须同步检查 `feature-test-playbook.md`

## 发布前必查
- 核对 `AGENTS.md`、`CONTRIBUTING.md`、`docs/20-engineering/spec-lifecycle.md` 是否存在且可读
- 核对 `docs/20-engineering/feature-test-playbook.md` 是否存在且可读
- 核对当前变更是否命中本表中的至少一类变更类型
- 若命中，确认对应事实来源文档已同步
- 确认 `docs/skill-hub-master-plan.md` 只记录进度，不承载正式规范
- 确认仓库内没有构建产物、系统垃圾文件和测试残留
- 运行 `infra/scripts/release-check.sh`
