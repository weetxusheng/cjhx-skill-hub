# 功能完成后测试执行手册

## 目的
本手册是 Skill Hub 在“功能开发、Bug 修复、重构、规则落地”完成后的统一测试入口。默认目标不是“跑几个命令看看”，而是确认：
- 代码行为正确
- 主流程没有回归
- 命中的正式规范已同步
- 当前变更达到可交付状态

## 适用范围
- 前端页面与交互改动
- 后端接口与 service 改动
- 权限、状态机、统计口径改动
- 数据库 schema、migration、seed 改动
- 运维、发布、恢复相关改动
- 因正式规范更新而触发的代码实现变更

## 执行前准备
### 先做变更识别
1. 对照 `docs/20-engineering/doc-update-matrix.md` 判断本次变更类型
2. 确认是否命中：
   - 权限模型
   - 状态机 / 审核发布流
   - 数据库 schema
   - API 字段 / 分页 / 错误
   - 后台工作台
   - 统计口径
   - 本地开发与发布
3. 若命中正式规范边界，先确认对应文档已更新，不允许只改代码不补规范

### 再做环境检查
- 数据库可连接
- migration 可执行
- API `.venv` 可用
- `pnpm` 依赖可用
- 开发期间默认保持本地项目在线，普通代码改动依赖热更新或自动重载，不把 `pnpm local:stop` 作为默认步骤
- 每次写完代码后，先执行 `pnpm local:ensure`，确认 API、admin-web、portal-web 仍在线；若有服务掉线，必须先补拉再测试
- 需要联调时，确认是否要执行 `pnpm seed:local-workbench`
- 需要的账号、端口、页面入口已知

### 默认环境命令
```bash
bash infra/scripts/local-infra.sh up
cd apps/api-server && .venv/bin/alembic upgrade head
pnpm local:ensure
pnpm seed:local-workbench
```

`pnpm seed:local-workbench` 不是每次必跑，只有以下情况建议执行：
- 需要手工检查审核中心 / 待发布 / 处理记录
- 当前数据库缺少 `submitted`、`approved`、`published` 等关键状态数据
- 需要验证统计与授权展示

## 分层测试模型
### `L0` 变更识别与环境准备
任何功能完成后都必须先执行 `L0`。

通过标准：
- 已识别变更类型
- 已确认需要同步的正式规范
- 已确认本地环境、数据库、依赖和测试数据是否可用

### `L1` 相关改动最小验证
适用于轻量页面、文案、样式、非规则性小改动，但仍然要求覆盖直接影响范围。

至少包含：
- 直接相关模块的构建、测试或 smoke
- 受影响页面的加载态、空态、错误态、权限不足态检查
- 与改动直接相关的手工验证

### `L2` 能力域回归
适用于会影响一个能力域正确性的改动，例如：
- 普通后端接口
- 工作台页面
- 组件交互
- 非 schema 级数据库查询
- 非核心规则的联动逻辑

至少包含：
- 相关后端测试
- 双前端构建
- 相关 Playwright / 手工 smoke
- 受影响能力域的关键主流程回归

### `L3` 全量回归 / 发布级验证
只要命中以下任一类，就必须直接升级到 `L3`：
- 权限模型
- 状态机 / 审核发布流
- 数据库 schema / migration
- API 契约
- 统计口径
- 发布、恢复、本地开发流程
- 关键工作台路径无法容忍回归的改动

至少包含：
- 后端全量 `pytest`
- 双前端 build
- 关键 Playwright smoke
- migration 验证
- `pnpm release:check`

## 变更类型到测试层级映射
| 变更类型 | 最低测试层级 | 必做项 |
|---|---|---|
| 前端页面 / 轻交互 | `L1` | 受影响前端 build、相关 smoke、手工状态检查 |
| 后端接口 / service | `L2` | 相关后端测试、双前端 build、相关联调 |
| 后台工作台 | `L2` | 双前端 build、相关 Playwright 或手工 smoke、受影响接口验证 |
| API 字段 / 分页 / 错误语义 | `L3` | 全量后端 pytest、双前端 build、相关 E2E、必要手工联调 |
| 权限模型 | `L3` | 全量后端 pytest、权限矩阵验证、相关页面权限 smoke |
| 状态机 / 审核发布流 | `L3` | 全量后端 pytest、审核发布主链路回归、相关 E2E |
| 数据库 schema / migration / seed | `L3` | migration、全量后端 pytest、联调数据检查、`pnpm release:check` |
| 统计口径 | `L3` | 全量后端 pytest、明细与汇总一致性检查、相关页面验证 |
| 运维 / 发布 / 恢复 | `L3` | `pnpm release:check`、相关 runbook 命令验证 |

## 现有测试资产与执行方式
### 后端
- 全量回归：
```bash
cd apps/api-server && .venv/bin/pytest -q
```
- 当前主测试文件：
  - `apps/api-server/tests/test_skill_workflow.py`
  - `apps/api-server/tests/test_skill_lists.py`
  - `apps/api-server/tests/test_production_features.py`

### 前端
- 管理后台 build：
```bash
pnpm --filter admin-web build
```
- 用户前台 build：
```bash
pnpm --filter portal-web build
```

### E2E / Smoke
- Playwright：
```bash
pnpm test:e2e
```
- 当前关键 smoke：
  - `tests/e2e/admin.spec.ts`
  - `tests/e2e/portal.spec.ts`

### 发布级校验
```bash
pnpm release:check
```

## 各层具体执行要求
### `L1` 最小验证
默认至少执行：
- 与改动直接相关的后端测试或接口联调
- 受影响前端应用 build
- `pnpm local:ensure`
- 受影响页面手工 smoke

推荐组合：
- 改 `portal-web`：`pnpm --filter portal-web build`
- 改 `admin-web`：`pnpm --filter admin-web build`
- 改单个后端能力域：跑相关 `pytest` 文件或相关接口联调

通过标准：
- 改动直接影响范围验证通过
- 没有明显构建错误
- 页面基本可打开，关键态无明显缺失

### `L2` 能力域回归
默认至少执行：
```bash
pnpm --filter admin-web build
pnpm --filter portal-web build
```

并补充：
- `pnpm local:ensure`
- 相关后端测试
- 相关 Playwright 或手工 smoke
- 受影响能力域的主流程验证

通过标准：
- 能力域关键路径可用
- 不只验证 happy path，还验证至少一类异常或权限场景

### `L3` 全量回归 / 发布级验证
默认执行：
```bash
bash infra/scripts/local-infra.sh up
cd apps/api-server && .venv/bin/alembic upgrade head
pnpm local:ensure
cd apps/api-server && .venv/bin/pytest -q
pnpm --filter admin-web build
pnpm --filter portal-web build
pnpm test:e2e
pnpm release:check
```

通过标准：
- 后端全量 pytest 通过
- 双前端 build 通过
- Playwright smoke 通过
- release-check 通过
- 手工 smoke 未发现阻断问题

## 手工 Smoke Checklist
### 通用
- 相关页面能正常打开
- 加载态、空态、错误态、权限不足态可用
- 改动后的文案、按钮、入口与权限一致

### 后台
- 管理员可登录后台
- 技能列表能打开
- 审核中心能看到 `submitted`
- 待发布能看到 `approved`
- 处理记录能看到最近动作
- 相关详情页可打开

### 前台
- portal 首页可打开
- 技能详情抽屉可打开
- 下载动作可触发
- 若改动涉及互动数据，验证点赞 / 收藏 / 下载展示

### 数据与规则
- 前台只读 `published`
- `approved` 不直接当线上版本
- 权限不足时返回可读错误
- 统计字段可追溯到明细或既定口径

## 结果分级
- `可合并`：命中的测试层级已执行，通过，且无已知阻断风险
- `仅本地通过`：本地验证通过，但仍有外部依赖、环境差异或未覆盖风险
- `不可交付`：命中测试未执行、关键项失败，或仍存在阻断问题

## Agent 输出模板
Agent 完成实现后，最终回复必须包含以下结构：

```text
测试层级：L1 / L2 / L3
执行项目：
- 命令或检查项 1：结果
- 命令或检查项 2：结果

未执行项目：
- 项目：未执行原因

结论：
- 可合并 / 仅本地通过 / 不可交付

风险：
- 剩余风险 1
- 剩余风险 2
```

若存在未执行项：
- 不允许静默跳过
- 必须写清阻塞原因
- 必须说明对交付结论的影响

## 默认规则
- 先判断变更类型，再决定测试层级，不允许凭感觉挑测试
- 开发、联调、手工 smoke、测试收尾阶段默认保持项目在线，除非用户明确要求或必须处理端口冲突，否则不要执行 `pnpm local:stop`
- 每次代码改动完成后，进入测试、联调、手工 smoke 或最终回复前，先执行 `pnpm local:ensure`
- 命中权限、状态机、数据库、API、统计、发布相关改动时，自动升级到 `L3`
- 文档、代码、测试三者缺一不可
- 若规范已变但测试未更新，视为变更未完成
