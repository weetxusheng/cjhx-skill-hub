# 门户主系统单点登录（网关参数）

## 场景

主系统在用户已登录态下跳转 Skill Hub **门户**（默认 `http://127.0.0.1:5173`），URL 上携带：

- `loginname`：经网关编码的十六进制字符串（UTF-8 字节再按约定 XOR 解码，见参考 Java）。
- `sign`：与主系统一致的签名字段（字节流参与 XOR，与历史 `MyEncode` 一致）。
- 其他查询参数（如 `ycOrderId`）由门户忽略。

## 对接步骤

1. 门户首屏读取查询参数；若存在 `loginname` 与 `sign`，**POST** `POST /api/auth/sso-portal`，JSON 体字段名与查询参数相同：`{ "loginname": "...", "sign": "..." }`。
2. 后端按 `app/services/sso_gateway_decode.py` 解码得到明文 `username`，与 `users.username` 匹配；成功则返回与普通密码登录相同的双令牌 + `user` 摘要。
3. 前端写入门户 `localStorage` 会话（与手动登录相同），并 **replace** 去掉敏感查询参数，避免地址栏泄露。
4. 本地库中需存在对应 `username` 且 `status=active` 的用户。

## 配置

| 环境变量 | 含义 | 默认 |
|----------|------|------|
| `SSO_PORTAL_ENABLED` | 是否开放该接口 | `true` |
| `SSO_PORTAL_RATE_LIMIT` | 限流（与 `enforce_rate_limit` 规则串一致） | `30/minute` |

生产环境若未使用单点，请将 `SSO_PORTAL_ENABLED=false`。

## 参考实现

- 算法参考：`docs/20-engineering/references/sso-gateway-MyEncode.java`
- Python 实现：`apps/api-server/app/services/sso_gateway_decode.py`

## 安全说明

- 该机制依赖主系统下发的 **loginname + sign 配对**；若第三方仅知算法而缺少主系统生成的签名，无法伪造有效参数。
- 失败时接口返回统一「单点登录失败」，避免通过响应区分「解码失败」与「用户不存在」。
