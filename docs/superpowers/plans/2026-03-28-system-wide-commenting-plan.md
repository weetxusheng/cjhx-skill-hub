# 全仓库补注释执行计划

## 1. 目标

在**整个 Skill Hub 代码仓库**内，按统一规范补齐「说明意图/边界/副作用/契约」的注释，避免仅复述代码。范围**不限于** `apps/api-server/app`，包含前后端应用、测试、脚本与基础设施脚本。

**事实来源（优先级）**

- `AGENTS.md`（Non-Negotiable Rules / 注释与 docstring）
- `docs/20-engineering/commenting-and-docstrings.md`
- `docs/20-engineering/backend-code-spec.md`、`docs/20-engineering/frontend-code-spec.md`（与分层一致时）

## 2. 范围矩阵（按交付单元）

| 单元 | 路径 | 注释类型 | 优先级 |
|------|------|----------|--------|
| API 应用 | `apps/api-server/app/` | 模块说明；`routes` 每个对外处理函数；`deps`/`core`/`schemas` 公开符号；`models` 类级一句话+关键字段；`repositories` 公开查询 | P0 |
| API 测试与工厂 | `apps/api-server/tests/`、`tests/support/` | 复杂 `fixture`/工厂函数、非常规 `conftest` 钩子 | P1 |
| API 脚本 | `apps/api-server/scripts/`（如 `seed_local_workbench_data.py`） | 文件头目的；大段步骤分区注释 | P1 |
| Alembic | `apps/api-server/alembic/versions/*.py` | 仅 `revision` 级说明「改什么表/为何」；**不写**与 migration 无关的长篇 | P2（低） |
| 管理后台 | `apps/admin-web/src/` | `pages/**/*.tsx` 交互约定；复杂 `components`/`lib` 契约；`store` 持久化策略 | P0 |
| 门户 | `apps/portal-web/src/` | 同上 | P0 |
| 基础设施脚本 | `infra/scripts/*.sh` | 已有中文说明处保持一致；新增脚本需头部用途 | P1 |
| 根配置 | `package.json`、`pnpm-workspace`、各 `vite.config.ts` | 仅当存在非显而易见配置时一行说明 | P3（可选） |

**明确低优先级或排除**

- 自动生成、锁文件、构建产物目录。
- 纯声明的 `d.ts`、无逻辑的 re-export 文件可仅保留必要单行。

## 3. 分层标准摘要

### 3.1 Python

- **Route**：每个 endpoint 函数 docstring：用途、鉴权依赖、主要错误语义（引用 service 即可不写业务长篇）。
- **Service / Repository**：公开函数（非 `_`）完整 docstring（意图、权限/状态边界、副作用）。
- **Model**：SQLAlchemy 模型类：类 docstring 1～3 句；字段仅当语义非自解释时注释。
- **Schema**：Pydantic 模型或公共构造：字段语义与校验约束。
- **Core**：`config`、`security`、`database` 等：模块头 + 每个公开函数说明。

### 3.2 前端（TypeScript/React）

- **`pages/**/*.tsx`**：文件入口附近「交互约定」：加载/空/错误/权限不足四态。
- **复杂组件**：props 契约、与 `queryKey`/mutation 失效策略相关的说明。
- **`lib/api.ts`**：若存在统一错误处理、base URL 策略，在文件头说明。

## 4. 分阶段执行（建议）

| 阶段 | 内容 | 完成定义 |
|------|------|----------|
| **A** | `apps/api-server/app/` 全量（`main`、`router`、`deps`、`core`、`api/routes`、`schemas`、`models`、`db`） | `ruff check` 通过；占位注释门禁通过 |
| **B** | `apps/admin-web/src` 未覆盖页面/组件与 `lib` | `pnpm --filter admin-web lint` |
| **C** | `apps/portal-web/src` 未覆盖页面/组件与 `lib` | `pnpm --filter portal-web lint` |
| **D** | `apps/api-server/tests` + `scripts` 高价值片段 | pytest 不受影响 |
| **E** | `infra/scripts` 与 Alembic 按需补一句 | `release-check` 仍通过 |

阶段 **A→C** 为产品主路径，建议顺序执行；**D/E** 可与 C 并行或收尾。

## 5. 验证与门禁（每阶段结束）

- `pnpm lint`
- `bash infra/scripts/check-comment-placeholders.sh`
- 后端：`cd apps/api-server && .venv/bin/ruff check app tests scripts`
- 命中 `docs/20-engineering/feature-test-playbook.md` 中对应层级时补跑测试

## 6. 当前进度快照（截至计划建立时）

- **已完成较多**：`app/services/` 多条线、`repositories/skills.py`、部分前端页面（工作台/治理/详情等）。
- **明显缺口**：`app/api/routes/*`、`app/core/*`（除零散外）、`app/models/*`、`app/schemas/*`、`main.py`、`router.py`、`deps.py` 多数文件；portal 部分组件；`scripts/seed_local_workbench_data.py` 体量大可分区注释。
- **本计划文件**用于后续 PR/迭代按阶段勾选，不替代 `docs/skill-hub-master-plan.md` 的进度记录。

## 7. 文档联动

若变更「注释规范」或门禁，需同步：`AGENTS.md`、`docs/20-engineering/commenting-and-docstrings.md`、`docs/20-engineering/code-review-guide.md`（见 `doc-update-matrix.md` 中代码规范类变更）。

前后端 HTTP 用法与 JSON 契约见 `docs/20-engineering/fullstack-api-usage-contract.md`（与 `api-and-testing.md` 配套）。
