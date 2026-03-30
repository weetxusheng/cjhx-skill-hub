# Docs Inventory & Drift Checklist（v1）

本清单用于做一次“全仓文档盘点”，并持续追踪文档漂移（docs drift）：代码/流程已变更但事实来源或指南未同步。

## A. 覆盖面（Coverage）
- 每个一级事实来源域至少存在一份可追溯主文档（source of truth）
  - 产品边界与术语：`docs/00-overview/`
  - 架构/权限：`docs/10-architecture/`
  - 审核/发布/授权/统计：`docs/30-product-flows/`
  - 工程规范与门禁：`docs/20-engineering/`
  - 运行/发布/恢复：`docs/40-runbooks/`、`docs/deploy/`
- 每个关键产品流（上传/审核/发布/授权/统计）都具备：
  - 流程步骤或状态机说明
  - 权限不足态与异常说明
  - 与 API/数据表/统计口径的对应关系

## B. 一致性与去重（Consistency & DRY）
- 同一事实（例如：审核流 `draft -> submitted -> approved -> published`）只在唯一主文档中定义
- 其他文档如需引用，只链接到主文档章节锚点，不复写定义

## C. 生命周期与责任（Lifecycle）
- 一级事实来源必须包含：
  - OWNER
  - Last reviewed
  - Change triggers（映射到 `docs/20-engineering/doc-update-matrix.md`）
- 与变更相关的 spec 必须包含可验收条款与测试计划

## D. 可验收（Testability）
- 权限/状态机/发布/统计口径相关文档必须给出可验证验收点，并指向：
  - API 测试：`apps/api-server/tests/...`
  - E2E：`tests/e2e/...`
  - 门禁脚本：`infra/scripts/...`
- UI 交互相关文档必须覆盖：
  - 加载态 / 空态 / 错误态 / 权限不足态

## E. 盘点输出格式（Inventory Output）
对每份文档建立条目：

```markdown
- [ ] Doc path: `docs/.../xxx.md`
  - 分类：一级事实来源/二级辅助/计划与进度/runbook
  - OWNER：xxx（若缺失则标记缺口）
  - Canonical 引用：`docs/.../main.md#anchor`（若该文档本身是主文档则写“self”）
  - Drift 风险：低/中/高（理由）
  - 缺口：列出具体缺失段落或验收条款
```

