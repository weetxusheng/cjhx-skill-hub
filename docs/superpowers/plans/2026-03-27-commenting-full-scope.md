# Full-Scope Commenting & Docstring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在不改变行为逻辑的前提下，为全仓关键代码补齐可维护的注释与 docstring，并通过门禁避免后续“零注释/漂移注释”回归。

**Architecture:** 先建立“注释契约（commenting contract）+ 模板 + 最小门禁”，再按模块批次补注释。每个批次必须能独立通过 `pnpm lint` 与必要测试，并以小提交粒度推进。

**Tech Stack:** Markdown docs、Python docstring、TS/React 块注释、现有 lint/quality/release 脚本。

---

## Task 1: Add a repository-wide Commenting Contract (规范落地)

**Files:**
- Create: `docs/20-engineering/commenting-and-docstrings.md`
- Modify: `docs/20-engineering/code-review-guide.md`
- Reference: `docs/superpowers/specs/2026-03-27-commenting-full-scope-design.md`

- [ ] **Step 1: Create `commenting-and-docstrings.md`**

```markdown
# 注释与 Docstring 规范（Commenting Contract）

> 目标：注释解释“为什么/约束/边界/契约”，不复述代码；并确保注释可追溯到事实来源与测试。

## 1. 注释写什么（允许）
- Intent（意图）：这段逻辑要保证的业务目标
- Invariants（不变量）：任何状态下必须成立的约束
- Boundaries（边界）：哪些状态/权限允许/禁止；禁止时系统如何表现
- Side effects（副作用）：审计、缓存失效、计数变更的发生时机
- Contracts（契约）：API 字段语义、分页/筛选规则、queryKey 组成规则

## 2. 注释不写什么（禁止）
- 复述代码（“这里把 x 加 1”）
- 复制粘贴业务规则到多个地方（必须链接唯一事实来源锚点）
- 用 TODO/TBD/WIP/FIXME 作为“未来再补”的占位（提交前必须清理）

## 3. Python docstring 最小模板
对外可调用/业务语义函数（routes/services/repositories 的 public 方法）必须至少包含：
- 一句话意图
- 输入/输出要点（只写关键字段）
- 关键边界：权限/状态机/审计/缓存（如适用）

示例（可直接复制）：

```python
def publish_version(db: Session, *, version_id: UUID, actor_user_id: UUID) -> AdminVersionDetail:
    \"\"\"Publish an approved version.

    Intent:
      - Move a version from `approved` into the published state, and enqueue it for public availability.
    Invariants:
      - Review lifecycle must follow `draft -> submitted -> approved -> published`.
      - Any write must emit an audit log entry.
    Side effects:
      - Cache invalidation happens after commit.
    References:
      - docs/30-product-flows/upload-review-release.md#... (canonical anchor)
    \"\"\"
    ...
```

## 4. 前端“交互契约注释”模板
页面与复杂组件入口必须写清楚 4 态优先级（加载/空/错误/权限不足）：

```ts
/**
 * Interaction contract:
 * - loading: show skeleton/spinner
 * - error: show error state with retry
 * - forbidden: show forbidden state (no blank screen)
 * - empty: show empty state with guidance
 */
```
```

- [ ] **Step 2: Update code review checklist to include comment contract**

在 `docs/20-engineering/code-review-guide.md` 的“代码细节检查清单”下追加一段：

```markdown
### 注释与契约（Commenting Contract）
- 是否在权限/状态机/统计口径/审计/缓存副作用点补了“意图/边界/副作用”说明？
- 前端关键页面是否明确 loading/empty/error/forbidden 四态的渲染契约？
- 是否出现 TODO/TBD/WIP/FIXME 形式的占位注释（不允许提交）？
```

- [ ] **Step 3: Verify**
Run: `pnpm lint`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add docs/20-engineering/commenting-and-docstrings.md docs/20-engineering/code-review-guide.md
git commit -m "docs: add commenting contract and review checklist"
```

---

## Task 2: Add a “No Placeholder Comments” Gate (最小门禁)

**Files:**
- Modify: `infra/scripts/check-doc-quality.sh` (ensure it doesn’t block on historical TODO mentions in docs)
- Create: `infra/scripts/check-comment-placeholders.sh`
- Modify: `infra/scripts/release-check.sh`

- [ ] **Step 1: Adjust doc quality gate placeholder rules**
目标：docs 门禁继续禁止 `TBD/WIP/FIXME`，但不因历史规范里提到 `TODO` 而阻塞发布。

- [ ] **Step 2: Create `check-comment-placeholders.sh`**

```bash
#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

cd "${ROOT_DIR}"

echo "Running placeholder comment checks..."

# 禁止在代码注释中留下占位
# 注意：这里不扫描 docs/，只扫描代码目录
TARGETS=(
  "${ROOT_DIR}/apps/admin-web/src"
  "${ROOT_DIR}/apps/portal-web/src"
  "${ROOT_DIR}/apps/api-server/app"
)

pattern='(TODO|TBD|WIP|FIXME)'

if command -v rg >/dev/null 2>&1; then
  if rg -n --hidden -S "${pattern}" "${TARGETS[@]}"; then
    echo "Placeholder comments found in code. Remove before committing." >&2
    exit 1
  fi
else
  if grep -R -n -E "${pattern}" "${TARGETS[@]}"; then
    echo "Placeholder comments found in code. Remove before committing." >&2
    exit 1
  fi
fi

echo "Placeholder comment checks passed."
```

- [ ] **Step 3: Wire it into `release-check.sh` (early)**
在 “Run doc quality gates” 后面、lint 前面加入：

```bash
bash "${ROOT_DIR}/infra/scripts/check-comment-placeholders.sh"
```

- [ ] **Step 4: Verify**
Run: `bash infra/scripts/check-comment-placeholders.sh`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add infra/scripts/check-comment-placeholders.sh infra/scripts/release-check.sh infra/scripts/check-doc-quality.sh
git commit -m "chore: gate placeholder comments in code"
```

---

## Task 3: Backend Docstrings — Phase 1 (services + permission/state/audit hotspots)

**Files:**
- Modify (seed list; extend as you go):
  - `apps/api-server/app/services/skills.py`
  - `apps/api-server/app/services/governance.py`
  - `apps/api-server/app/services/skill_access.py`
  - `apps/api-server/app/services/audit.py`
  - `apps/api-server/app/api/routes/*.py` (only routes touched by services above)

- [ ] **Step 1: Add module-level docstring to each hotspot module**

Python module header template:

```python
\"\"\"<Module role in one sentence>.

Key contracts:
- Permission model: global permission + skill-scope grants (see docs/10-architecture/data-and-permissions.md#...)
- Review lifecycle: draft -> submitted -> approved -> published (see docs/30-product-flows/upload-review-release.md#...)
- Audit: any write must emit audit_logs (see docs/10-architecture/...#... or docs/30-product-flows/...#...)
\"\"\"
```

- [ ] **Step 2: Add function docstrings for all public service functions**
Docstring minimum fields: Intent + boundaries (permission/state) + side effects (audit/cache) + references.

- [ ] **Step 3: Add docstrings for complex helpers**
Definition of “complex”: contains permission checks, state branching, audit/cache write, or non-trivial query composition.

- [ ] **Step 4: Verify**
Run: `pnpm lint:api`
Expected: PASS

- [ ] **Step 5: Commit (small)**

```bash
git add apps/api-server/app/services
git commit -m "docs(code): add docstrings to core backend services"
```

---

## Task 4: Backend Docstrings — Phase 2 (repositories + schema contracts)

**Files:**
- Modify:
  - `apps/api-server/app/repositories/**/*.py`
  - `apps/api-server/app/schemas/**/*.py` (only if schema fields need docstring/context)

- [ ] **Step 1: Repository function docstrings**
For each public query method:
- what it returns (DTO/schema)
- key filters/pagination rules
- performance considerations (indexes/avoid N+1) when non-obvious

- [ ] **Step 2: Verify**
Run: `pnpm lint:api`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add apps/api-server/app/repositories apps/api-server/app/schemas
git commit -m "docs(code): add repository and schema docstrings"
```

---

## Task 5: Frontend Comments — Admin Web (pages + critical modals)

**Files:**
- Modify:
  - `apps/admin-web/src/pages/**/*.tsx`
  - `apps/admin-web/src/components/**/*.tsx` (only complex modals/panels)

- [ ] **Step 1: Page-level interaction contract**
At the top of each page component: add the “loading/empty/error/forbidden” contract comment.

- [ ] **Step 2: Permission/state branching comments**
Where a page chooses between routes/actions based on capabilities, add a short comment explaining:
- which capability/permission gates it
- why “menu visible” and “route reachable” must share the same predicate

- [ ] **Step 3: Verify**
Run: `pnpm --filter admin-web lint`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add apps/admin-web/src/pages apps/admin-web/src/components
git commit -m "docs(code): add interaction contract comments to admin web"
```

---

## Task 6: Frontend Comments — Portal Web (pages + key components)

**Files:**
- Modify:
  - `apps/portal-web/src/pages/**/*.tsx`
  - `apps/portal-web/src/components/**/*.tsx`
  - `apps/portal-web/src/lib/**/*.ts` (only where permission/types/usage guide normalization is non-obvious)

- [ ] **Step 1: Page-level interaction contract**

- [ ] **Step 2: Data fetching + queryKey contract comments**
Where React Query is used:
- add a short comment near queryKey construction rules when non-obvious
- add comment explaining invalidate strategy where it’s business critical

- [ ] **Step 3: Verify**
Run: `pnpm --filter portal-web lint`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add apps/portal-web/src/pages apps/portal-web/src/components apps/portal-web/src/lib
git commit -m "docs(code): add interaction contract comments to portal web"
```

---

## Task 7: Full Verification Sweep

**Files:**
- N/A (verification only)

- [ ] **Step 1: Ensure local stack online**
Run: `pnpm local:ensure`
Expected: all healthy

- [ ] **Step 2: Lint**
Run: `pnpm lint`
Expected: PASS

- [ ] **Step 3: Release check (heavy)**
Run: `bash infra/scripts/release-check.sh`
Expected: PASS

---

## Notes / Guardrails
- 每个 commit 保持“小步可回滚”：按模块/目录切片推进，不要一次改几百文件。
- 若发现某模块“解释意图”需要事实来源支撑，优先补到 `docs/10-architecture/` 或 `docs/30-product-flows/`，代码注释只放最短引用链接。

