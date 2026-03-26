# 上传、审核、发布流程

## 上传类型
### 新 Skill 首次上传
1. 具备 `skill.upload` 的用户上传 ZIP
2. 创建新 `skill`
3. 创建首个 `skill_version`
4. 状态默认是 `draft`

### 已有 Skill 上传新版本
1. 命中已有 `skill.slug`
2. 创建新的 `skill_version`
3. 不影响当前线上版本
4. 状态默认是 `draft`

## 状态定义
- `draft`：已上传但尚未提审，可继续编辑
- `submitted`：已进入待审核队列
- `approved`：审核通过，但还未上线，只能在待发布中心发布
- `published`：当前线上版本，前台可见
- `archived`：历史已下线版本，可用于回滚
- `rejected`：审核被拒绝，可修改后再次提审

## 提审
1. 具备 `skill.submit` 且有对应 skill 授权的用户提交版本
2. 状态变为 `submitted`
3. 版本出现在审核中心

## 审核
1. 审核中心只处理 `submitted`
2. 审核人查看：
  - manifest
  - README
  - changelog
  - usage guide
  - 最近审核记录
3. 通过后状态变为 `approved`
4. 拒绝后状态变为 `rejected`
5. 拒绝必须填写原因
6. 审核结果进入处理记录

## `approved` 与 `published` 的区别
- `approved`：质量或流程上通过，但尚未上线
- `published`：当前线上正式版本
- 前台只读 `published`
- 后台待发布中心只读 `approved`

## 多个 `approved` 版本并存
- 允许同一个 skill 同时存在多个 `approved`
- 待发布中心默认按：
  1. 最近审核通过时间倒序
  2. 若时间相同，按版本创建时间倒序
- 发布人必须显式选择要发布的目标版本

## 待发布
1. `approved` 版本进入待发布中心
2. 发布人统一从待发布中心执行上线
3. 推荐路径是：
  - 审核中心 -> 待发布 -> 发布
4. 不推荐从版本详情直接找按钮发布，版本详情只作为补充入口

## 发布
1. 当前线上版本自动归档
2. 目标版本进入 `published`
3. `skills.current_published_version_id` 指向新版本
4. 前台立即生效

### 术语约定
- 当前线上版本：当前 `published` 版本
- 最新版本：按创建时间最新的版本，不一定线上
- 待发布版本：处于 `approved` 的版本

## 回滚
1. 选择某个 `archived` 版本
2. 执行 rollback
3. 旧历史版本重新成为 `published`
4. 回滚后前台详情、列表、下载目标都切到回滚版本

## 禁止路径
- 未经审核通过直接发布
- 跳过待发布中心就把 `approved` 当线上版本
- 用“最新版本”误代替“线上版本”
- 让 draft/rejected 元数据污染前台线上显示
