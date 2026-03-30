# 文档更新责任矩阵

## 使用方式
任何功能变更都先看“变更类型”，再按本表同步对应文档、测试和 runbook。

| 变更类型 | 必须更新的文档 | 必须检查的实现 |
|---|---|---|
| 权限模型 | `docs/10-architecture/data-and-permissions.md` `docs/30-product-flows/skill-authorization-and-metrics.md` | 鉴权、菜单、按钮、测试 |
| 状态机 / 审核流 | `docs/30-product-flows/upload-review-release.md` `docs/30-product-flows/admin-workbench.md` | service、工作台接口、测试 |
| 数据库 schema | `docs/20-engineering/data-and-db-handbook.md` 对应架构文档 | migration、seed、测试 |
| API 字段 / 分页 / 错误 / HTTP 契约 | `docs/20-engineering/api-testing-and-release.md` | route、schema、前端 `apiRequest`、错误展示、测试 |
| 门户主系统单点登录（`loginname`/`sign`） | `docs/20-engineering/sso-portal-gateway.md` | `sso_gateway_decode.py`、`/auth/sso-portal`、`portal-web` 首屏消费、`SSO_PORTAL_*` |
| 模块边界 / 目录落点 / 跨层调用 | `docs/10-architecture/domain-module-map.md` `docs/10-architecture/repository-structure.md` | route/service/repository/page 结构、导入边界 |
| 页面结构 / 抽屉 / 工作台布局 | `docs/20-engineering/page-spec-template.md` `docs/20-engineering/frontend-guide.md` `docs/30-product-flows/core-page-specs.md` | 页面区块、稳定 `id`、状态矩阵、E2E |
| UI 样式系统 / 交互细节（按钮、间距、字号、阴影、圆角、表单、弹窗） | `docs/20-engineering/frontend-guide.md` | token、样式、E2E 断言、视觉一致性 |
| 前后端代码实现细节（命名、分层、异常、测试写法） | `docs/20-engineering/engineering-handbook.md` | 代码风格一致性、review checklist、单测与 E2E |
| lint / 代码质量门禁 / 例外登记 | `docs/20-engineering/engineering-handbook.md` `docs/20-engineering/code-quality-debt-register.md` | `pnpm lint`、`release-check.sh`、allowlist、拆分计划 |
| 仓库结构 | `docs/10-architecture/repository-structure.md` | 目录落点、导入边界 |
| 后台工作台 | `docs/30-product-flows/admin-workbench.md` `docs/20-engineering/frontend-guide.md` | admin 页面和 E2E |
| 统计口径 | `docs/30-product-flows/skill-authorization-and-metrics.md` | 汇总、明细、测试 |
| 测试门禁 / 回归流程 | `docs/20-engineering/api-testing-and-release.md` `docs/50-prompts/qa-guide.md` `AGENTS.md` | 测试命令、Agent 执行流程、交付结论 |
| 本地开发与发布 | `docs/40-runbooks/*` 或 `docs/deploy/*` | 脚本、命令、smoke |

## 评审要求
- 评审时若发现改动命中本表但未更新文档，视为必须修复项
- 若变更跨越多个域，必须同时更新多份文档
- 若变更影响测试门禁、完成定义或 Agent 测试收尾流程，必须同步检查 `api-testing-and-release.md`

## 发布前必查
- 核对 `AGENTS.md`、`CONTRIBUTING.md`、`docs/20-engineering/README.md` 是否存在且可读
- 核对 `docs/20-engineering/engineering-handbook.md`、`docs/20-engineering/frontend-guide.md`、`docs/20-engineering/data-and-db-handbook.md`、`docs/20-engineering/api-testing-and-release.md`、`docs/20-engineering/docs-governance.md`、`docs/20-engineering/code-quality-debt-register.md` 是否存在且可读
- 核对 `docs/10-architecture/domain-module-map.md`、`docs/20-engineering/page-spec-template.md` 是否存在且可读
- 核对当前变更是否命中本表中的至少一类变更类型
- 若命中，确认对应事实来源文档已同步
- 确认 `docs/skill-hub-master-plan.md` 只记录进度，不承载正式规范
- 确认仓库内没有构建产物、系统垃圾文件和测试残留
- 运行 `infra/scripts/check-doc-quality.sh`
- 运行 `infra/scripts/release-check.sh`
