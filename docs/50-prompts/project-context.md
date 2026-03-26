# Project Context Prompt

## 先读什么
1. `AGENTS.md`
2. `docs/00-overview/project-map.md`
3. `docs/10-architecture/system-architecture.md`
4. `docs/10-architecture/data-and-permissions.md`
5. `docs/30-product-flows/upload-review-release.md`

## 你在做什么
- 你在维护一个企业内 Skill 平台
- 你的默认目标是保证：
  - 审核发布链路正确
  - 权限边界清晰
  - 统计口径一致
  - 后台工作台可运营

## 禁止什么
- 禁止绕过审核发布状态机
- 禁止绕过全局权限 + skill 级授权两层模型
- 禁止把后台写操作做成无审计
- 禁止只改代码不改对应事实来源文档

## 完成定义
- 代码、文档、测试三者口径一致
- 新能力能明确落到对应工作台或页面
