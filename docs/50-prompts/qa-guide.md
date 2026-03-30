# QA Prompt Guide

## 先读什么
1. `docs/20-engineering/api-testing-and-release.md`
3. `docs/30-product-flows/upload-review-release.md`
4. `docs/30-product-flows/skill-authorization-and-metrics.md`

## 做什么
- 先识别本次变更类型，再按 `api-testing-and-release.md` 选择 `L1`、`L2`、`L3` 测试层级
- 开发过程中默认保持项目在线，普通改代码依赖热更新或自动重载
- 每次写完代码、准备测试或收尾前，先执行 `pnpm local:ensure`
- 每次写完代码、准备测试或收尾前，先执行 `pnpm lint`
- 覆盖上传、提审、审核、待发布、发布、回滚整条链路
- 验证 skill 级授权
- 验证 detail capability、分页接口和下载脱敏是否与文档一致
- 验证收藏、点赞、下载统计一致性
- 验证演示 seed 是否能直接展示待审核、待发布、已拒绝、已归档、已回滚

## 禁止什么
- 不要把 `pnpm local:stop` 当作默认开发动作
- 不要只测 happy path
- 不要忽略权限不足、状态冲突、空数据、错误态和脏 seed
- 不要凭感觉挑测试项，必须先做变更识别
- 不要静默跳过无法执行的测试

## 完成定义
- 已按变更类型命中对应测试层级
- 已执行 `pnpm local:ensure`，确认本地项目仍在线
- 已执行 `pnpm lint`
- 后端回归通过
- 前端构建通过
- 关键 smoke 路径通过
- 输出统一测试结果摘要、未执行项、阻塞原因和残余风险
