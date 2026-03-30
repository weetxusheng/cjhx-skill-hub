# 工程规范导航

## 目的
`docs/20-engineering/` 是 Skill Hub 的工程实现与交付规则层。本目录不再按“前端一份、前端代码细则一份、UI 一份、测试一份、门禁一份”继续细拆，而是收口成少量主手册，降低阅读切换成本。

## 必读顺序
### 做前端页面、抽屉、弹窗
1. `engineering-handbook.md`
2. `frontend-guide.md`
3. `page-spec-template.md`
4. 与当前页面相关的 `docs/30-product-flows/`

### 做后端接口、service、repository
1. `engineering-handbook.md`
2. `data-and-db-handbook.md`
3. `api-testing-and-release.md`

### 做数据库 schema、migration、seed
1. `data-and-db-handbook.md`
2. `docs/10-architecture/data-and-permissions.md`
3. `api-testing-and-release.md`

### 做测试、联调、发布收尾
1. `api-testing-and-release.md`
2. `docs-governance.md`
3. `docs/40-runbooks/`

### 做规范补充、评审、文档同步
1. `docs-governance.md`
2. `engineering-handbook.md`
3. `code-quality-debt-register.md`（如涉及质量例外）

## 文件职责
| 文件 | 职责 | 什么时候看 |
|---|---|---|
| `engineering-handbook.md` | 前后端实现规则、代码细节、评审重点、质量门禁 | 日常开发默认必读 |
| `frontend-guide.md` | 前端专项规则：目录边界、组件与 Hook 分层、样式系统、命名、设计 token、可访问性、性能 | 做前端页面或样式时必读 |
| `data-and-db-handbook.md` | 表设计、字段规范、索引约束、migration/seed 手册 | 改数据结构时必读 |
| `api-testing-and-release.md` | HTTP 契约、前后端 API 用法、测试分层、smoke、发布门禁 | 改接口或收尾时必读 |
| `docs-governance.md` | 文档分层、更新矩阵、补充机制、模板要求 | 改规范或评审时必读 |
| `page-spec-template.md` | 页面规格模板 | 新增或重构关键页面前必读 |
| `code-quality-debt-register.md` | 代码质量例外台账 | 命中超长文件或临时例外时必读 |

## 默认规则
- `engineering-handbook.md` 是前后端与代码细节的唯一主入口，不再拆成前端/后端/代码细则多份并行事实来源。
- `frontend-guide.md` 是前端页面实现、样式系统、命名与设计 token 的专项补充；做前端改动时，它与 `engineering-handbook.md` 共同构成事实来源。
- `data-and-db-handbook.md` 是数据模型与数据库落地的唯一主入口，不再区分“数据库原则”和“数据模型规格”两份文档。
- `api-testing-and-release.md` 同时覆盖 API 契约、测试层级与发布门禁，不再要求先后阅读三份文档才能收尾。
- `docs-governance.md` 同时承担文档责任矩阵、生命周期和模板规则；计划文件不能替代这里的正式规范。
- 只有 `page-spec-template.md` 与 `code-quality-debt-register.md` 保持独立，分别作为高频模板和动态台账。
