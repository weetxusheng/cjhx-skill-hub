# 代码质量技术债登记

## 目的
本文件记录当前因历史包袱、页面复杂度或链路测试原因暂时放行的代码质量例外。它不是“永久白名单”，而是持续拆分和收债的清单。

## 当前例外
| 路径 | 规则 | 当前原因 | 退出条件 |
|---|---|---|---|
| `apps/admin-web/src/components/AdminLayout.tsx` | 前端单文件 > 250 行 | 工作区 tab、菜单、登出状态仍集中在一个布局组件 | tab 状态管理与布局渲染拆分 |
| `apps/admin-web/src/pages/governance/RolesPage.tsx` | 前端单文件 > 250 行 | 列表、表单、权限矩阵仍在同一页 | 角色表单和权限矩阵拆分 |
| `apps/admin-web/src/pages/governance/UsersPage.tsx` | 前端单文件 > 250 行 | 用户列表、角色分配和状态动作仍集中 | 用户角色弹窗和过滤逻辑拆分 |
| `apps/admin-web/src/pages/workbench/DashboardPage.tsx` | 前端单文件 > 250 行 | 工作台概览卡、快捷入口和数据摘要耦合 | 摘要卡片抽成私有组件 |
| `apps/admin-web/src/pages/detail/SkillDetailPage.tsx` | 前端单文件 > 250 行 | 技能详情聚合多 query、授权状态与区块编排仍集中在一页 | 授权区与统计区拆成路由子段或懒加载子页 |
| `apps/admin-web/src/pages/workbench/SkillsPage.tsx` | 前端单文件 > 250 行 | 技能主档表格列定义与筛选条仍同文件 | 列配置与筛选条抽成模块或子组件 |
| `apps/portal-web/src/pages/MarketplacePage.tsx` | 前端单文件 > 250 行 | 技能广场列表、筛选、抽屉状态编排仍较重 | 筛选区和结果区继续拆分 |
| `apps/api-server/app/repositories/skills.py` | 后端单文件 > 400 行 | 技能域只读查询仍集中在一个 repository | public/admin/stats 查询拆分 |
| `apps/api-server/app/services/governance.py` | 后端单文件 > 400 行 | 分类、用户、角色、审计治理逻辑仍在同一 service | 治理子域 service 拆分 |
| `apps/api-server/app/services/skills.py` | 后端单文件 > 400 行 | 技能详情、列表、互动统计与授权查询仍混合 | public/admin/metrics service 拆分 |
| `apps/api-server/scripts/seed_local_workbench_data.py` | 后端单文件 > 400 行 | 本地工作台演示数据脚本仍是集中构造 | fixture builder 按场景拆分 |
| `apps/api-server/tests/test_skill_workflow.py` | 测试文件 > 600 行 | 审核发布链路集成测试仍在同一文件 | 按“上传/审核/发布/授权”拆分测试文件 |

## 使用规则
- 新增例外时，必须同步更新：
  - 本文件
  - `infra/config/code-quality-allowlist.txt`
- 解决例外时，必须同步移除登记和 allowlist
- 评审时若发现新增超长文件但未登记，视为 blocker
