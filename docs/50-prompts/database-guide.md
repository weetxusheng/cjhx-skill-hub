# Database Prompt Guide

## 先读什么
1. `docs/20-engineering/database-guide.md`
2. `docs/10-architecture/data-and-permissions.md`

## 做什么
- 用 migration 明确表达新的事实结构
- 保持 seed、测试和生产数据路径一致
- 为审核、授权、统计补齐约束和索引

## 禁止什么
- 不要只改 ORM 不改 migration
- 不要新增“靠应用层约定”的弱约束
- 不要让 seed 与测试 fixture 脱节

## 完成定义
- migration 可跑
- 新 seed 可导入
- 关键回归测试可通过
