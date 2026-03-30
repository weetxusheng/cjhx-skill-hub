# API、测试与发布手册

## 目的
本手册统一 Skill Hub 的 HTTP 契约、前后端 API 用法、测试分层、smoke 清单与发布阻断规则。接口开发和测试收尾都以这里为准。

## HTTP 与 JSON 契约
### 成功响应
```json
{
  "code": 0,
  "message": "ok",
  "data": {}
}
```

### 失败响应
- 统一返回可读 `message`
- 如有更细说明，使用 `detail`
- 响应中保留 `request_id` 便于排障
- `401/403/404/409` 必须稳定区分，不得全部落为 `400`

### 分页与 capability
- 分页接口统一返回：`items`、`total`、`page`、`page_size`
- 工作台与详情接口若涉及按钮显隐，优先由后端返回 capability
- capability 只表达“当前是否允许”，不重复回传前端可推导的信息

## 前后端 API 调用约定
- 默认基地址：`VITE_API_BASE_URL`，本地指向 `http://127.0.0.1:8000/api`
- JSON 请求使用 `Content-Type: application/json`
- `FormData` 上传不得手写 `Content-Type`
- 需登录接口传 `Authorization: Bearer <access_token>`
- 前端 `apiRequest` 只取响应体中的 `data`
- 二进制下载（如后台 `GET /api/admin/versions/{version_id}/package`）不走 `apiRequest` JSON 解包，使用 `fetch` + Blob 触发保存；不计入前台 `download_count`
- 公开健康检查路径在 `/health/*`，不与业务接口混用
- 门户主系统单点：`POST /api/auth/sso-portal`，体为 `{ "loginname": "<hex>", "sign": "<string>" }`，成功响应与密码登录相同；细节见 [`sso-portal-gateway.md`](./sso-portal-gateway.md)

## API 设计规则
- 参数命名使用业务语义名，如 `page`、`page_size`、`category`
- 工作台列表应返回足够摘要，避免前端 N+1
- 详情接口应同时回答“展示什么”和“当前能做什么”
- 错误 message 要能直接给前端使用

## 测试分层
### `L0`
- 识别变更类型
- 确认需要同步的文档
- 确认本地环境、数据库、依赖和测试数据

### `L1`
- 轻量页面、样式、文案、小交互
- 至少执行：`pnpm local:ensure`、`pnpm lint`、受影响应用 build、相关手工 smoke

### `L2`
- 能力域级改动，如普通接口、工作台页面、组件交互
- 至少执行：相关后端测试、双前端 build、相关 Playwright 或手工 smoke

### `L3`
- 权限、状态机、数据库 schema、API 契约、统计口径、发布流程
- 默认执行：
```bash
bash infra/scripts/local-infra.sh up
cd apps/api-server && .venv/bin/alembic upgrade head
pnpm local:ensure
pnpm lint
cd apps/api-server && .venv/bin/pytest -q
pnpm --filter admin-web build
pnpm --filter portal-web build
pnpm test:e2e
pnpm release:check
```

## 当前必须覆盖的回归线
- 上传 -> 提审 -> 审核 -> 待发布 -> 发布 -> 回滚
- 前台上传中心直传 ZIP 与“我的上传记录”
- skill 级授权与 capability
- 收藏 / 点赞 / 下载统计一致性
- 审核中心、待发布、处理记录可达性

## Smoke Checklist
- `pnpm local:ensure` 通过
- 管理员可登录后台
- 技能列表、审核中心、待发布、处理记录可打开
- 前台技能广场与详情抽屉可打开
- 前台上传中心首屏直接可拖拽 ZIP
- 前台上传中心列表只展示当前用户自己的上传记录
- 下载、点赞、收藏链路无明显回退

## 发布阻断项
以下任一失败都视为阻断：
- `pnpm lint` 失败
- 后端全量 `pytest` 失败
- 任一前端 build 失败
- 关键 Playwright smoke 失败
- migration 无法从空库升级
- `infra/scripts/release-check.sh` 失败

## 默认联调与发布前命令
```bash
pnpm local:ensure
pnpm lint
cd apps/api-server && .venv/bin/pytest -q
pnpm --filter admin-web build
pnpm --filter portal-web build
pnpm test:e2e
pnpm release:check
```

## 测试结果要求
- 最终结论只能是：`可合并`、`仅本地通过`、`不可交付`
- 必须列出已执行项、未执行项、阻塞原因和残余风险
