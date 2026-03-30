# Docs System Optimization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **Goal:** Build a consistent, verifiable documentation governance system so changes to architecture/permissions/workflows are always discoverable, testable, and up-to-date.
>
> **Architecture:** Treat docs as a product with (1) a taxonomy (where each doc belongs), (2) a lifecycle/spec-contract (how docs get authored/updated/reviewed), and (3) quality gates (how we detect drift/duplication). Optimize incrementally: add standards + automation scaffolding first, then migrate existing docs module-by-module.
>
> **Tech Stack:** Markdown, repository docs folders, existing CI/shell scripts (if available), and lightweight grep-like checks replaced by `rg`-based scripts.
---

### Task 1: Create a Docs Inventory & Drift Checklist
**Files:**
- Create: `docs/superpowers/plans/_artifacts/docs-inventory-checklist.md`

- [ ] **Step 1: Define what “good docs” means (checklist)**

```markdown
# Docs Inventory & Drift Checklist (v1)

## A. Coverage
- 每个“一级事实来源”（如架构/权限/状态机/发布流程）都至少有一份可追溯的“主文档”（source of truth）。
- 每个关键交互（上传/审核/发布/授权/统计）都有：流程图或步骤列表 + 异常/权限不足态说明 + 与数据/表/接口的对应关系。
- 每个统计口径都有：明细/聚合表引用或计算来源说明。

## B. Consistency & DRY
- 同一概念（例如：审核流状态机、权限两层模型）不会在多个文档里用不同口径复述。
- 每处“复述”都必须指向 source of truth（超链接到唯一主文档锚点）。

## C. Lifecycle
- 每个 spec 类文档必须标明：适用范围、变更触发条件、预计更新频率、责任人（OWNER）。
- 如果代码/接口已经实现，文档必须匹配：至少包含 API/行为层面的验收条款。

## D. Testability
- 与权限/状态机相关的文档必须给出可验证的验收用例（对应到现有 API/测试文件路径）。
- 与前端页面相关的文档必须给出至少 4 类 UI 态：加载态/空态/错误态/权限不足态。

## E. Tooling hooks (optional)
- 有可执行脚本检查：链接是否失效、关键关键字是否仍出现、模板是否被遵守。
```

- [ ] **Step 2: Produce an inventory map**

```markdown
Inventory Map Output Format (paste into a tracking doc):

- [ ] Doc path: `docs/.../xxx.md`
  - 分类：一级事实来源/二级辅助/流程/规范/运行手册
  - OWNER：xxx
  - 依赖的 source of truth：`docs/.../main.md#anchor`
  - 是否存在 DRIFT 风险：低/中/高（理由：代码已变更但文档未更新）
  - 缺口：列出具体缺失段落或验收条款
```

- [ ] **Step 3: Run drift scan manually (initial phase)**
   - 使用仓库内 `rg` 搜索关键术语（例如“draft -> submitted -> approved -> published”“audit_logs”“权限两层模型”）确认是否只有单一主文档解释它们。
   - 对于出现多份不同解释的关键词，记录冲突列表并标注要迁移/合并的目标。

### Task 2: Define Docs Taxonomy, Ownership, and “Source of Truth” Rules
**Files:**
- Create: `docs/20-engineering/docs-taxonomy-and-ownership.md`

- [ ] **Step 1: Write the taxonomy contract**

```markdown
# Docs Taxonomy & Ownership (v1)

## 1) Categories
- 一级事实来源（Source of Truth）：架构/权限/状态机/发布与审核流程/数据与统计口径
- 二级辅助文档（Assistant）：指南、示例、运行说明、扩展说明
- 变更记录（Change log）：仅用于演进摘要，不覆盖事实来源

## 2) Ownership
- 每个一级事实来源必须有 OWNER（人/团队）+ 最后审阅日期 + 联系方式
- 非一级事实来源允许多个贡献者，但最终要链接到唯一主文档解释事实

## 3) Update Rules
- 当代码触及权限/状态机/数据库/发布流程：必须同时更新对应一级事实来源文档，并补回归测试条款。
- 当更新 UI 交互：必须覆盖加载/空/错误/权限不足态，并与前端规范章节对齐。
```

- [ ] **Step 2: Add “canonical anchor” strategy**
   - 为每个主文档核心章节设置锚点（例如 `#审核流`、`#权限两层`），并在其他文档只链接到锚点而不复写定义。

### Task 3: Introduce a Universal Doc Template + Per-Doc-Type Templates
**Files:**
- Create: `docs/20-engineering/doc-templates/primary-facts.md`
- Create: `docs/20-engineering/doc-templates/spec-doc.md`
- Create: `docs/20-engineering/doc-templates/runbook.md`

- [ ] **Step 1: Primary facts template**

```markdown
# Primary Facts Template

## Purpose
一句话说明该文档作为“唯一事实来源”解决什么问题。

## Scope
覆盖范围（系统域、功能域、时间/版本范围）。

## Definitions (Canonical)
- 核心术语 A：一段简洁定义（不得在其他文档重复定义）
- 核心术语 B：一段简洁定义

## Workflow / State Machine
步骤或状态图（含合法/非法迁移说明）。

## Permission Model
明确“两层模型”：
1) 全局后台权限决定可进入页面/接口类型
2) skill 级授权决定可操作具体对象

## Audit & Data Lineage
- 后台写操作：必须写到 `audit_logs`
- 统计口径：给出明细/聚合来源

## Verification (Acceptance)
列出验收点，并指向测试用例/接口路径。
```

- [ ] **Step 2: Spec doc template (for changes)**

```markdown
# Spec Doc Template

## Summary
要解决的问题、非目标、风险点。

## Requirements
逐条列出可验证的需求，每条至少包含验收方式（测试/接口/日志）。

## Implementation Impact
- files expected to change
- API/DB impacts
- UI impacts

## Rollout Plan
灰度/回滚策略与监控指标（如果适用）。
```

### Task 4: Update Doc Update Matrix and Link Every Relevant Change Type
**Files:**
- Modify: `docs/20-engineering/doc-update-matrix.md` (to extend/clarify mapping)

- [ ] **Step 1: Ensure matrix entries are executable**
   - 每一行变更类型必须映射到：
     - 必须同步更新的事实来源文档清单
     - 必须执行/新增的测试类型（API/前端/E2E/回归）
     - 必须更新的模板章节（例如 Primary Facts / Spec Doc / Runbook）

- [ ] **Step 2: Add “doc drift triggers”**
   - 权限/状态机/发布/统计口径类变更：默认进入较高验收门禁等级。

### Task 5: Add Documentation Quality Gates (Automated Checks)
**Files:**
- Create: `infra/scripts/check-doc-quality.sh`
- Modify: `infra/scripts/release-check.sh` (if release flow exists)

- [ ] **Step 1: Implement a lightweight doc linter (no heavy parsing)**

```bash
#!/usr/bin/env bash
set -euo pipefail

# 目标：快速发现链接/模板/关键术语的“明显漂移”

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

cd "$ROOT_DIR"

# 1) 禁止出现明显占位词（示例）
if rg -n --hidden -S "TBD|TODO:.*(更新|补全)|placeholder" docs; then
  echo "Doc quality gate failed: placeholders found"
  exit 1
fi

# 2) 关键锚点是否仍出现（示例关键词，你可按仓库现状调整）
rg -n "draft -> submitted -> approved -> published" docs/ || true

echo "Doc quality gate passed (basic checks)."
```

- [ ] **Step 2: Wire into existing release/test pipeline**
   - 如果仓库已有 `release-check.sh`，把 `check-doc-quality.sh` 加在发布前。

### Task 6: Migrate Existing Docs Incrementally (Non-breaking Refactor)
**Files:**
- Modify: existing docs gradually (module-by-module; keep links stable via aliases)

- [ ] **Step 1: Choose the first migration slice**
   - 按“权限/状态机/发布审核链路/数据与统计口径”优先级迁移。

- [ ] **Step 2: For each slice, apply 3 rules**
   - 将定义挪到唯一主文档（其他文档只链接）
   - 每个关键流程补齐：加载/空/错误/权限不足态（若涉及 UI）
   - 补回归验收条款（指向测试文件路径）

### Task 7: Establish Continuous Maintenance Process
**Files:**
- Create: `docs/20-engineering/doc-maintenance-process.md`

- [ ] **Step 1: Write maintenance SLA**
   - 每次涉及主文档的 PR 必须包含：文档变更摘要、受影响系统、验收方式、链接到测试。

### Self-Review (for the plan author)
1. Spec coverage: 所有一级事实来源类别是否被纳入（架构/权限/状态机/发布/数据统计）？
2. Placeholder scan: 计划中是否存在 `TODO/TBD`？
3. Executability: 每个任务是否能独立落地，不依赖“必须先搞定其他任务才能开始”？

### Execution Handoff
建议执行顺序：
1) Task 1-3（先建立治理框架和模板）
2) Task 4-5（把更新矩阵和质量门禁落到流程里）
3) Task 6-7（迁移与持续维护）

两种执行方式：
1. Subagent-Driven（推荐）：我会按 Task 粒度逐个派发子代理，并在任务间做简短回顾
2. Inline Execution：在当前会话里直接按任务做（但通常会慢）

你希望用哪种方式推进？

