# Review Release Prompt Guide

## 先读什么
1. `docs/30-product-flows/upload-review-release.md`
2. `docs/30-product-flows/admin-workbench.md`
3. `docs/10-architecture/data-and-permissions.md`

## 做什么
- 审核中心只处理 `submitted`
- 待发布只处理 `approved`
- 处理记录只负责追溯
- 版本详情页是补充入口

## 禁止什么
- 不要把 `approved` 当成线上版本
- 不要把发布入口只藏在版本详情
- 不要让 draft/rejected 数据污染前台

## 完成定义
- 审核、待发布、处理记录三条工作台路径清晰
- 发布新版本自动归档旧版本
- 回滚后前台立即切换
