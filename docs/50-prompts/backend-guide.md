# Backend Prompt Guide

## 先读什么
1. `docs/20-engineering/engineering-handbook.md`
2. `docs/10-architecture/data-and-permissions.md`
3. `docs/30-product-flows/upload-review-release.md`

## 做什么
- 把状态机、授权和审计放在 service 层收口
- 保证工作台接口足够结构化
- 让公开读接口和后台治理接口口径一致

## 禁止什么
- 不要在 route 拼复杂 SQL
- 不要只做全局权限、不做 skill 级授权
- 不要忘记缓存失效和审计

## 完成定义
- 状态流转、权限、审计、缓存失效都覆盖
- 接口足够支持前端工作台，不需要靠前端拼逻辑补洞
