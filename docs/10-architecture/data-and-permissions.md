# 数据与权限模型

## 核心表
- `skills`
- `skill_versions`
- `version_reviews`
- `favorites`
- `skill_likes`
- `download_logs`
- `roles`
- `permissions`
- `role_permissions`
- `user_roles`
- `skill_role_grants`
- `skill_user_grants`
- `audit_logs`

## Global Permissions
### 作用
由 `roles -> role_permissions` 聚合得到，决定用户是否：
- 可以进入某类后台页面
- 可以调用某类后台接口
- 可以看到某些治理数据或导出能力

### 原则
- 全局权限是第一层门槛
- 没有全局权限时，即使 skill 上有 grant，也不能越权进入对应能力域
- 例如：没有 `skill.publish` 的用户，即使在某个 skill 上被授予 `publisher` scope，也不能发布

## Skill-Level Grants
### 类型
- `skill_role_grants`：给角色授予某个 skill 的 scope
- `skill_user_grants`：给具体用户授予某个 skill 的 scope

### Scope 定义
- `owner`
- `maintainer`
- `reviewer`
- `publisher`
- `viewer`

### 默认新 skill 的授权
- 上传人自动获得：
  - `owner`
  - `maintainer`
- 如果系统中存在默认 reviewer/publisher 角色，则新 skill 自动授予：
  - reviewer 角色 -> `reviewer`
  - publisher 角色 -> `publisher`

## 判定顺序
1. 先检查全局权限是否允许进入该能力域
2. 再检查 skill 级授权
3. 若当前 skill 没有任何 role grant 和 user grant：
  - 回退到全局权限模型
  - 视为该 skill 尚未启用细粒度授权
4. 若当前 skill 存在任意 grant：
  - 进入白名单模式
  - 只有命中对应 scope 的用户或角色才可操作该 skill

## 多 Grant 合并规则
- user grant 与 role grant 叠加
- 多个 role grant 叠加
- 最终取并集，不做“拒绝型”覆盖
- 当前版本不支持显式 deny

## 角色/用户失效规则
- 角色停用：
  - 其全局权限立即失效
  - 该角色关联的 skill role grant 视为不可用
- 用户停用：
  - 全局权限失效
  - skill user grant 仍保留记录，但运行时不生效
- 用户被移除角色：
  - 该角色带来的全局权限和 skill grant 同步失效

## Scope 与能力映射
| Scope | 可做的事 |
|---|---|
| `owner` | 查看、编辑、上传版本、提审、审核、发布、归档、回滚、配置授权 |
| `maintainer` | 查看、编辑、上传版本、提审 |
| `reviewer` | 查看、审核 |
| `publisher` | 查看、发布、归档、回滚 |
| `viewer` | 查看 |

## 全局权限与 Skill Scope 映射
| 全局权限 | 需要的最小 Skill Scope |
|---|---|
| `skill.view` | `viewer` 及以上 |
| `skill.edit` | `maintainer` 或 `owner` |
| `skill.upload` | `maintainer` 或 `owner` |
| `skill.submit` | `maintainer` 或 `owner` |
| `skill.review` | `reviewer` 或 `owner` |
| `skill.publish` | `publisher` 或 `owner` |
| `skill.archive` | `publisher` 或 `owner` |
| `skill.rollback` | `publisher` 或 `owner` |

## 设计默认值
- Skill grant 不支持层级继承
- 不支持“仅某版本授权”，授权粒度固定为 skill
- 不支持用户直配全局 permission，只通过角色授予

## Current Implementation State
- 当前实现以全局权限作为第一层门槛，skill grant 作为第二层限制
- 当某个 skill 尚未配置任何 grant 时，运行时回退到全局权限模型
- 当某个 skill 已存在任意 grant 时，运行时进入白名单模式
- 当前产品行为以本文件和 `docs/30-product-flows/skill-authorization-and-metrics.md` 为准，历史计划文件不作为权限事实来源

## 统计口径
### 汇总字段
- `favorite_count`：收藏总数
- `like_count`：点赞总数
- `download_count`：下载总数

### 明细来源
- 收藏：`favorites`
- 点赞：`skill_likes`
- 下载：`download_logs`

### 一致性要求
- 明细表为事实来源
- `skills` 冗余计数字段用于高频读取
- 若发生口径争议，以明细表重新汇总结果为准
