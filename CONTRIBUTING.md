# Skill Hub 贡献规范

## 先读什么
开始任何开发前，固定按以下顺序阅读：
1. `AGENTS.md`
2. `docs/00-overview/project-map.md`
3. 与当前任务相关的 `docs/10-architecture/`
4. 与当前任务相关的 `docs/20-engineering/`
5. 与当前任务相关的 `docs/30-product-flows/`
6. `docs/20-engineering/README.md`

若只看 `docs/skill-hub-master-plan.md` 就开始修改，视为流程不合规。

## 贡献流程
1. 明确任务属于哪类变更：权限、状态机、数据库、API、页面、统计、部署
2. 查阅 `docs/20-engineering/docs-governance.md`
3. 在同一轮变更中同步更新：
   - 代码
   - 文档
   - 测试
   - 必要的 runbook
4. 开发期间默认保持本地项目在线，普通代码改动依赖热更新；不要把停服务再启动作为默认动作
5. 进入联调、手工 smoke、测试收尾和最终提交前，执行 `pnpm local:ensure`
6. 执行 `pnpm lint`
7. 运行 `infra/scripts/release-check.sh`
8. 确认仓库没有构建产物、系统垃圾文件和无效脚手架残留

## 文档与代码的关系
- `docs/10-architecture/`、`docs/30-product-flows/` 是当前行为的正式事实来源
- `docs/20-engineering/` 是实现和交付规则
- `docs/40-runbooks/` 是操作手册
- `docs/50-prompts/` 只服务协作执行，不得覆盖正式规范
- `docs/skill-hub-master-plan.md` 只记录阶段计划与历史进展

## 必须同步更新文档的场景
- 改权限模型、skill 授权、角色能力
- 改审核、待发布、回滚状态机
- 改数据库 schema、migration、seed
- 改 API 字段、分页、错误码、响应结构
- 改后台工作台结构、关键运营路径
- 改统计口径、明细可见范围、脱敏规则
- 改本地开发、发布或恢复流程
- 改 lint、代码细节规则、文件拆分阈值或例外清单

详细映射见 `docs/20-engineering/docs-governance.md`。

## 提交前检查
- `infra/scripts/release-check.sh`
- 后端测试通过
- 前端构建通过
- 关键 Playwright smoke 可运行
- 关键事实来源文档已同步
- 仓库无以下残留：
  - `.DS_Store`
  - `dist/`
  - `*.tsbuildinfo`
  - `vite.config.js`
  - `vite.config.d.ts`
  - `test-results/`

## 规范补充机制
规范不是一次写死，新增或修正规则时按 `docs/20-engineering/docs-governance.md` 执行。
