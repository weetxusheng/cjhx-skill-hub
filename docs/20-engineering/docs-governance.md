# 文档治理规则

## 目的
本手册统一 Skill Hub 文档体系的职责分层、更新矩阵、生命周期与模板要求。凡是“改代码时该补哪份文档”“先改文档还是先改代码”的问题，都以这里为准。

## 文档分层与事实来源
### 一级事实来源
- `docs/00-overview/`：产品边界、系统地图、术语
- `docs/10-architecture/`：系统结构、模块边界、权限模型、仓库结构
- `docs/20-engineering/`：工程实现、数据库、测试、发布、文档治理
- `docs/30-product-flows/`：审核发布、授权、工作台与页面实例规格
- `docs/40-runbooks/`：本地运行、发布、恢复、排障

### 二级辅助
- `docs/50-prompts/`：AI/协作代理执行提示，不得覆盖一级事实来源
- `docs/skill-hub-master-plan.md`：阶段计划与进度，不承担正式规范职责

## 变更类型 -> 必须更新哪些文档
| 变更类型 | 必更文档 |
|---|---|
| 权限模型 / skill 授权 | `docs/10-architecture/data-and-permissions.md`、相关产品流文档 |
| 审核 / 待发布 / 回滚状态机 | `docs/30-product-flows/upload-review-release.md`、`docs/30-product-flows/admin-workbench.md` |
| 数据库 schema / 索引 / 冗余统计 | `data-and-db-handbook.md`、相关架构文档 |
| API 字段 / 分页 / 错误 / HTTP 契约 | `api-testing-and-release.md` |
| 页面结构 / 抽屉 / 工作台布局 | `frontend-guide.md`、`page-spec-template.md` 或对应页面规格文档、相关产品流文档 |
| 前端样式系统 / design token / 命名 / 可访问性 / 性能 | `frontend-guide.md` |
| 代码细节规则 / 评审重点 / 门禁 | `engineering-handbook.md`、`code-quality-debt-register.md`（如命中例外） |
| 测试门禁 / 回归流程 / 发布前检查 | `api-testing-and-release.md`、`AGENTS.md`、`docs/50-prompts/qa-guide.md` |
| 本地开发 / 发布 / 恢复 | `docs/40-runbooks/` 或 `docs/deploy/` |

## 先改文档还是先改代码
- 权限、状态机、API 契约、统计口径、表设计：先补或同步补文档。
- 样式、轻微文案、非规则性小重构：可先改代码，但若触及规范边界，必须同轮补文档。
- 文档未同步，视为变更未完成。

## Owner 与维护频率
- 每份核心文档必须有明确 owner。
- 核心文档建议保留：
  - `Last reviewed`
  - `Change triggers`
- 影响 `release-check.sh` 的文档必须长期可读、路径稳定。

## 模板规则
- 关键页面规格统一用 `page-spec-template.md`
- 动态质量例外统一登记在 `code-quality-debt-register.md`
- 其余模板要求以“固定章节”方式内嵌到主文档，不再单独保留 `doc-templates/`

## 文档失配处理
- 计划文件与正式规范冲突：以正式规范为准
- prompt 文档与正式规范冲突：立即修 prompt 文档
- 代码与正式规范冲突：同一轮修代码或修文档，并补测试

## 发布前必查
- `AGENTS.md`、`CONTRIBUTING.md`、`docs/20-engineering/README.md` 可读
- `engineering-handbook.md`、`data-and-db-handbook.md`、`api-testing-and-release.md`、`docs-governance.md`、`page-spec-template.md`、`code-quality-debt-register.md` 存在
- `infra/scripts/release-check.sh` 与当前文档路径一致
- `check-comment-contracts.sh` 与 `engineering-handbook.md` 的注释要求一致
- 若命中质量例外，`code-quality-debt-register.md` 与 allowlist 一致

## 生命周期规则
- 改架构、权限、状态机、API、统计口径时，必须同步补一级事实来源
- 改测试门禁、回归流程、交付完成定义时，必须同步补 `api-testing-and-release.md`、`AGENTS.md` 和 `docs/50-prompts/qa-guide.md`
- 改 lint、文件拆分阈值、评审 blocker 时，必须同步补 `engineering-handbook.md`
- `release-check.sh` 是治理机制的一部分；改它时必须同步补本文件
