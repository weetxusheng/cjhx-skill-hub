# Frontend Prompt Guide

## 先读什么
1. `docs/20-engineering/engineering-handbook.md`
2. `docs/30-product-flows/admin-workbench.md`
3. 与当前页面相关的产品流文档

## 做什么
- 让后台工作台更顺畅
- 让 portal 用户更快看到 skill
- 确保权限显隐、状态提示和操作反馈一致

## 禁止什么
- 不要重新引入角色名硬编码
- 不要把关键操作藏到深层详情页
- 不要漏掉 loading / empty / error / forbidden

## 完成定义
- 页面有完整状态处理
- 页面与后端字段语义一致
- 审核中心、待发布、处理记录、skill 详情的数据面信息够运营使用
- 页面内所有可定位的“区域块”（例如 `Card`、筛选区、列表 `Table` 容器、表单区块、`Modal/Drawer` 内容区等）都必须在区域根节点添加稳定的 `id`（kebab-case，页面 slug 前缀），以便定位与自动化
- 审核中心里的版本详情优先通过“可编辑弹窗”承载，减少跳出工作台的上下文切换
- `admin-web` 详情页模块之间统一 `16px` 间距，避免混乱排版
