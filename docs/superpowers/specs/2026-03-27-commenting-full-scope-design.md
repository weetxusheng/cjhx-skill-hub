# Full-Scope Commenting & Docstring Design Spec

## Context
当前仓库代码整体缺少注释（几乎为“零注释”）。在存在权限两层模型、审核/发布状态机、审计落库、统计口径与前端权限渲染的前提下，缺少注释会显著降低可维护性与评审效率。

本设计用于系统性补充注释，使其：
- 解释“为什么”（业务意图、不可变约束、不变量）
- 解释“边界”（状态机合法迁移、权限不足行为）
- 解释“契约”（数据结构/接口契约/缓存与审计时机）
- 并避免注释漂移（注释必须与 docs/tests 相互可追溯）。

## Goal
在不改变任何行为逻辑的前提下，完成全量补注释：
- Python：为关键模块/公共函数添加 docstring，并对权限/状态机/审计/缓存副作用点做意图说明。
- TypeScript/React：为关键组件/复杂交互/权限渲染分支添加“交互契约注释”，必要处补充类型/查询/错误处理意图。

## Non-goals
- 不做大规模重构（拆分文件/改架构仅为注释服务的情况除外，但默认不触发）。
- 不引入新的运行时依赖。
- 不试图把代码“重复复制”为注释（注释不复述代码，而解释取舍与契约）。

## Approaches (选择与推荐)
### Approach A: Docstring-first（推荐）
- Python：对所有“对外可调用/承担业务语义/包含关键副作用”的函数添加 docstring。
- TS/React：对复杂渲染/权限分支/副作用块添加少量块注释，强调交互契约与错误处理。
- 优点：可维护性提升最大，注释与结构强绑定；风险可控。
- 缺点：产出量仍然较大，但比“对每行都注释”更可行。

### Approach B: Contract-only
- 仅为权限/状态机/审计/缓存/统计口径相关函数写注释，其余尽量不动。
- 优点：注释更集中，产出少。
- 缺点：当代码逻辑较复杂时仍缺少“为什么”的解释。

### Approach C: Ultra-complete（不推荐）
- 对大部分函数、每个分支都加注释，接近“代码逐行注释”。
- 优点：短期阅读门槛最低。
- 缺点：注释漂移概率高、维护成本高、评审成本高。

本设计推荐 Approach A。

## Commenting Contract（规则）
### 1) 注释内容类型
- Intent（意图）：这段逻辑要保证的业务目标是什么
- Invariants（不变量）：任何状态下必须成立的约束
- Boundaries（边界）：哪些状态/权限允许/禁止，禁止时系统如何表现
- Side effects（副作用）：审计落库、缓存失效、计数增减等发生在什么时机
- Contracts（契约）：接口/字段/查询参数规则；例如 `queryKey` 必含哪些维度

### 2) Python docstring 规范
- 顶部/模块：说明该模块在系统中的角色（权限/审核/统计等）
- 函数：只写关键解释，不复述 SQL/JQ/赋值细节
- 关键词：
  - 状态机：`review_status` / `draft/submitted/approved/published/archived` 的合法含义与作用点
  - 权限：指明使用的 permission 字符串与 scope 集合之间关系
  - 审计：说明必须调用 `audit_log` helper 的时机与字段含义
  - 缓存：说明 cache key 形态与 invalidation 触发点

### 3) TS/React “交互契约注释”规范
- 页面/组件入口：注释加载态/空态/错误态/权限不足态的渲染优先级
- 权限相关：注释“菜单可见”和“路由可达”共用同一判定函数的理由
- 表单与操作：注释提交/回滚/失败时的用户反馈策略
- 数据请求：注释关键 `queryKey` 组成规则与 invalidate 行为

### 4) 去漂移策略
- 注释必须可追溯到事实来源：
  - 权限/状态机：链接/引用到 `docs/10-architecture/` 或 `docs/30-product-flows/` 的章节锚点（在注释中用 URL/路径即可）
  - 统计口径：引用对应文档段落
- 不允许在生产代码出现 `TODO/TBD` 形式的未完成占位注释。

## Coverage Plan（全量补注释的“选取规则”）
为了“全量但可控”，采用以下选择规则：
- Python
  - 公开/对路由可达函数：必须有 docstring（routes、services）
  - repository：对外查询函数 + 含多表聚合/筛选的查询必须有 docstring
  - 私有 helper：若包含权限判断、状态分支、审计/缓存副作用，必须有 docstring；否则在函数较短且自解释的情况下可不补。
- TypeScript/React
  - `src/pages/**`：所有页面组件入口补充交互契约注释
  - 复杂 modal/drawer/detail panel：补充权限与错误处理说明
  - 一般的 display-only components：仅在 props/数据形态不直观时补注释

## Testing & Verification
- 行为不变，注释不应影响运行
- 验证仍需：
  - `pnpm lint`
  - `pnpm lint:api`（ruff check）
  - `pnpm test:e2e`（若 comment 改动波及关键路径）
- 若引入任何脚本/门禁变更，需要同步运行 `infra/scripts/release-check.sh`。

## Risks
- 注释漂移（当状态机/权限逻辑变更时注释未更新）
  - 缓解：注释引用 docs 锚点；并把注释更新纳入 `doc-update-matrix` 的变更类型范畴。
- 产出过大导致评审压力
  - 缓解：采用 bite-sized patch（一次改动一个模块/一个页面族群），并在 PR/提交粒度控制。

## User Approval Gate
如果你认可上面的 Approaches（推荐 A）与 Contract（注释内容类型/去漂移策略/覆盖规则），请回复“确认”，我就进入下一阶段：生成实现 Plan（writing-plans）并按模块切任务执行。

