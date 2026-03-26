# 后端开发规范

## 分层约束
### Route
- 负责鉴权、参数解析、返回封装
- 可做：依赖注入、轻量查询参数处理
- 禁止：复杂 SQL、跨实体事务编排、缓存失效策略

### Service
- 负责业务状态机、事务、审计、缓存失效、写模型
- 必须承载：
  - 上传
  - 提审
  - 审核
  - 发布
  - 回滚
  - 授权变更
  - 统计聚合写入

### Repository
- 负责复杂读取、聚合、工作台列表查询
- 禁止：状态流转、副作用

## 鉴权清单
- 全局权限由 `require_permissions(...)` 控制
- 单 skill 权限由 `ensure_skill_scopes(...)` 控制
- 新增 skill 相关接口时，必须同时考虑：
  - 是否需要后台全局权限
  - 是否需要 skill 级授权
  - 是否需要状态检查

## 状态机要求
- 非法流转统一返回 `409 Conflict`
- 审核拒绝必须要求 comment
- 发布和回滚必须放在事务中执行
- 发布成功后必须维护：
  - `skills.current_published_version_id`
  - `skills.latest_version_no`
  - `skills.published_at`
- 回滚后前台详情和列表读取的线上版本必须立即变化

## 审计要求
- 后台所有写操作必须写 `audit_logs`
- 至少记录：
  - actor
  - action
  - target_type
  - target_id
  - request_id
  - before_json
  - after_json

## 缓存要求
- 可缓存：
  - 公开分类列表
  - 公开技能详情
  - 高频只读列表
- 必须失效的场景：
  - publish
  - rollback
  - skill 主档编辑
  - 点赞/收藏变更
  - 影响公开展示的数据更新

## 错误码约定
- `400`：请求内容不合法
- `401`：未登录或 token 失效
- `403`：权限不足
- `404`：对象不存在或不对当前用户公开
- `409`：状态冲突、重复版本、非法流转

## Skill 相关接口新增时的必查项
1. 全局权限是否正确
2. skill 级授权是否正确
3. 当前版本状态是否允许
4. 是否需要写 `audit_logs`
5. 是否需要清缓存
6. 是否需要同步更新冗余统计或主档字段
