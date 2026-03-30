# Skill Hub Collaboration Guide

## Purpose
本文件是 Skill Hub 仓库的协作总入口。无论是人工开发、AI 代理、代码评审还是测试验收，都先从这里判断：
- 先读哪些文档
- 哪些文档是事实来源
- 发生某类变更时必须同步哪些规范
- 什么情况下只看计划文件，什么情况下必须看架构与流程文档

## Read Order
### 新成员、AI 代理、第一次进入仓库
1. `docs/00-overview/project-map.md`
2. `docs/00-overview/product-boundaries.md`
3. `docs/10-architecture/system-architecture.md`
4. `docs/10-architecture/data-and-permissions.md`
5. `docs/10-architecture/domain-module-map.md`
6. `docs/30-product-flows/upload-review-release.md`
7. `docs/30-product-flows/core-page-specs.md`
8. `docs/20-engineering/README.md`
9. 与当前任务相关的 `docs/20-engineering/` 和 `docs/50-prompts/`

### 做功能开发前
1. `docs/10-architecture/repository-structure.md`
2. `docs/10-architecture/domain-module-map.md`
3. 对应技术栈的开发规范；前端改动额外读取 `docs/20-engineering/frontend-guide.md`
4. 对应产品流文档
5. `docs/skill-hub-master-plan.md` 中当前阶段和 Next Task

### 做代码评审前
1. `docs/20-engineering/engineering-handbook.md`
2. 当前变更涉及的架构与流程文档
3. `docs/20-engineering/docs-governance.md`

### 做测试或发布前
1. `docs/20-engineering/api-testing-and-release.md`
2. `docs/40-runbooks/local-development.md`
3. `docs/40-runbooks/release-and-recovery.md`
4. `docs/deploy/`

## Source Of Truth
### 一级事实来源
- 产品边界与术语：`docs/00-overview/`
- 系统架构、仓库结构、权限模型：`docs/10-architecture/`
- 开发规范、测试规范、评审规范、文档更新矩阵：`docs/20-engineering/`
- 审核、发布、授权和统计口径：`docs/30-product-flows/`
- 运行、发布、恢复：`docs/40-runbooks/`

### 二级辅助文档
- `docs/50-prompts/`：面向 AI/协作代理的执行指南，不能覆盖一级事实来源
- `docs/skill-hub-master-plan.md`：只负责阶段计划、进度与下一步，不承载正式规范

### 发生冲突时的优先级
1. `docs/10-architecture/` 与 `docs/30-product-flows/`
2. `docs/20-engineering/`
3. `docs/40-runbooks/`
4. `docs/50-prompts/`
5. `docs/skill-hub-master-plan.md`

## Non-Negotiable Rules
- 不要只参考单个页面代码推断业务规则，优先看 `docs/10-architecture/` 和 `docs/30-product-flows/`。
- 正式审核流固定为：`draft -> submitted -> approved -> published`，其中 `approved` 必须先进入待发布队列。
- 权限判断固定为两层：
  - 全局后台权限决定能否进入某类页面或接口。
  - skill 级授权决定能否操作某个具体 skill。
- 后台写操作必须写 `audit_logs`。
- 数据库结构变更必须同步更新 Alembic migration、对应架构文档和测试。
- 设计或修改表结构、索引、冗余统计与明细关系时，必须同时遵守 `docs/20-engineering/data-and-db-handbook.md`。
- 设计或修改模块边界、目录落点、跨层调用关系时，必须同时遵守 `docs/10-architecture/domain-module-map.md`。
- 设计或修改关键页面、抽屉、弹窗时，必须先补或同步补页面规格，模板见 `docs/20-engineering/page-spec-template.md`。
- 新增页面或关键交互必须补加载态、空态、错误态和权限不足态。
- 所有提交类交互都必须提供 loading、防重复提交和明确的成功 / 失败反馈。
- 删除、停用/启用、授权移除、审核通过/拒绝、发布、归档、回滚以及任何会改变线上状态、权限范围或可见性的动作，必须二次确认。
- 任何统计字段都必须能追溯到明细表或明确的汇总口径。
- 代码注释与 docstring 默认使用简体中文；仅在引用协议关键字、标准库 API 名称或不可翻译术语时保留英文原词。
- 后端 `api/routes/`、`services/`、`repositories/`、`core/`、`db/`、`scripts/` 的公开函数（非 `_` 开头）必须具备 docstring，至少说明：意图、关键边界（权限/状态/异常）与副作用（审计/缓存/计数）。
- 后端 `core/`、`db/`、`models/`、`schemas/`、`scripts/` 模块必须具备模块级说明，明确职责、边界和禁止事项；`models/`、`schemas/` 不要求为每个字段逐条写注释，但关键状态和 JSON 字段必须可追溯。
- 前端 `apps/*/src/pages/**/*.tsx` 页面组件，以及 `apps/*/src/App.tsx` 这类应用壳层组件，必须在组件入口附近补“交互约定”注释，明确加载态/空态/错误态/权限不足态；禁止权限不足直接空白页。
- 前端页面壳层中承载登录、SSO、上传入口、全局会话恢复等关键动作的函数，必须补一句意图注释，不允许整段关键流程完全靠代码自解释。
- 前端 `apps/*/src/components/**` 与页面 `_components/` 必须补“组件约定”注释；`apps/*/src/lib/**` 必须补“模块约定”注释；`apps/*/src/store/**` 必须补“状态约定”注释。
- 前端目录边界、组件分层、命名、样式系统、颜色/字号/阴影/圆角、可访问性与性能规则，统一以 `docs/20-engineering/frontend-guide.md` 为准；做前端改动时必须同步遵守。
- 做任何功能开发、修复、重构后，进入收尾阶段前必须读取并执行 `docs/20-engineering/api-testing-and-release.md`。
- 做实现细节相关改动时，必须同时遵守 `docs/20-engineering/engineering-handbook.md`，并清理或登记代码质量例外。
- 开发期间默认保持本地项目在线，不要为了普通改代码、联调、手工 smoke 或测试收尾主动执行 `pnpm local:stop`。
- API 使用 `uvicorn --reload`，前端使用 Vite dev server；普通代码改动默认依赖热更新或自动重载，不单独手工重启整套项目。
- 每次写完代码，进入联调、手工 smoke、测试收尾或最终回复前，必须先执行 `pnpm local:ensure`，确认本地项目仍在线。
- 每次写完代码，进入测试收尾前，必须执行 `pnpm lint`。
- 若改动导致服务退出、热更新失败或端口异常，再执行 `pnpm local:ensure` 补拉；只有用户明确要求或必须清端口时，才允许执行 `pnpm local:stop`。
- 先按变更类型匹配测试层级，再执行对应测试，不允许凭感觉挑测试。
- 命中权限、状态机、数据库、API、统计、发布相关改动时，必须自动升级测试层级。
- 最终回复必须包含测试结果摘要；若有未执行项，必须说明阻塞原因和残余风险。
- 只有文档、代码、测试三者都完成，变更才算完成。

## What To Update When
详见 `docs/20-engineering/docs-governance.md`。这里给出最常见映射：
- 改权限：同步 `docs/10-architecture/data-and-permissions.md`、`docs/30-product-flows/skill-authorization-and-metrics.md`、相关测试
- 改审核流：同步 `docs/30-product-flows/upload-review-release.md`、`docs/30-product-flows/admin-workbench.md`、相关测试
- 改仓库结构：同步 `docs/10-architecture/repository-structure.md`、`docs/10-architecture/domain-module-map.md`
- 改表设计 / 索引 / 统计结构：同步 `docs/20-engineering/data-and-db-handbook.md`
- 改 API / HTTP 契约 / 测试门禁：同步 `docs/20-engineering/api-testing-and-release.md`
- 改页面结构 / 抽屉 / 工作台布局：同步 `docs/20-engineering/engineering-handbook.md`、`docs/20-engineering/frontend-guide.md`、`docs/20-engineering/page-spec-template.md` 或对应页面规格文档
- 改前端样式系统、设计 token、命名、组件边界或可访问性：同步 `docs/20-engineering/frontend-guide.md`
- 改核心页面实例规格：同步 `docs/30-product-flows/core-page-specs.md`
- 改测试门禁或回归流程：同步 `docs/20-engineering/api-testing-and-release.md`、`docs/50-prompts/qa-guide.md`、`AGENTS.md`
- 改 lint、代码质量门禁或例外规则：同步 `docs/20-engineering/engineering-handbook.md`、`docs/20-engineering/code-quality-debt-register.md`、`AGENTS.md`
- 改发布/恢复流程：同步 `docs/40-runbooks/release-and-recovery.md` 或 `docs/deploy/`

## Prompt Docs
- 项目上下文：`docs/50-prompts/project-context.md`
- 前端实现：`docs/50-prompts/frontend-guide.md`
- 后端实现：`docs/50-prompts/backend-guide.md`
- 数据库与 migration：`docs/50-prompts/database-guide.md`
- 审核发布与后台工作台：`docs/50-prompts/review-release-guide.md`
- 测试与验收：`docs/50-prompts/qa-guide.md`

## Current Delivery Focus
- 文档体系细化
- 审核中心、待发布、处理记录工作台
- skill 级授权与运营数据面
- 测试数据、自动化回归与 smoke checklist

## Execution Order
### 做任何开发、修复、重构前
1. 先确认任务属于哪一类：
   - 架构 / 权限 / 状态机
   - 前端页面 / 交互
   - 后端接口 / 数据库
   - 运维 / 发布 / 恢复
2. 按任务类型读取一级事实来源文档
3. 若涉及模块划分、表设计、页面结构、代码拆分，再补读：
   - `docs/10-architecture/domain-module-map.md`
   - `docs/20-engineering/data-and-db-handbook.md`
   - `docs/20-engineering/page-spec-template.md`
   - `docs/20-engineering/engineering-handbook.md`
4. 再读取对应 `docs/20-engineering/` 规范
5. 最后才参考 `docs/50-prompts/` 和 `docs/skill-hub-master-plan.md`

### 做实现时
- 先按 `docs/20-engineering/docs-governance.md` 判断要同步哪些文档、测试和 runbook
- 普通实现过程中保持项目在线，优先依赖热更新，不要把“停服务再启动”作为默认动作
- 每次代码改动完成后，先执行 `pnpm local:ensure`，再做手工验证、联调和测试收尾
- 每次代码改动完成后，先执行 `pnpm lint`；若命中代码质量例外，必须同步更新 debt register 和 allowlist
- 每次新增或修改注释后，必须执行“注释门禁”检查（`bash infra/scripts/check-comment-placeholders.sh` 与 `bash infra/scripts/check-comment-contracts.sh`）并确认通过
- 功能完成后，必须按 `docs/20-engineering/api-testing-and-release.md` 判断测试层级并执行对应测试
- 若代码现状与文档冲突，先修正文档或实现，不允许“先记在脑子里”
- 若发现历史计划和当前实现冲突，以 `docs/10-architecture/`、`docs/30-product-flows/` 为准

### 做评审和发布时
- 评审先看 `docs/20-engineering/engineering-handbook.md`
- 测试收尾先看 `docs/20-engineering/api-testing-and-release.md`
- 发布前必须跑 `infra/scripts/release-check.sh`
- 若关键事实来源文档未更新，视为变更未完成

## Doc Mismatch Handling
- 若 `docs/skill-hub-master-plan.md` 与正式规范冲突：
  - 视为历史演进记录
  - 不能作为当前行为依据
- 若 `docs/50-prompts/` 与一级事实来源冲突：
  - 立即修正 prompt 文档
  - 不允许按 prompt 文档覆盖架构或流程事实
- 若代码与一级事实来源冲突：
  - 先确认是实现落后还是文档过期
  - 必须在同一轮变更中修正其一，并补测试

## Spec Lifecycle
- 规范补充机制详见 `docs/20-engineering/docs-governance.md`
- 默认规则：
  - 改架构、权限、状态机、API、统计口径，先补或同步补文档
  - 改表结构、索引、模块边界、页面结构、文件拆分策略，先补或同步补对应规格文档
  - 改测试门禁、回归流程、交付完成定义，先补或同步补 `docs/20-engineering/api-testing-and-release.md`、`docs/50-prompts/qa-guide.md`、`AGENTS.md`
  - 改 lint、代码细节硬规则、文件拆分阈值或例外清单，先补或同步补 `docs/20-engineering/engineering-handbook.md`、`docs/20-engineering/code-quality-debt-register.md`
  - 文档未同步视为未完成变更
  - 发布前检查脚本会校验关键文档和仓库清洁度
