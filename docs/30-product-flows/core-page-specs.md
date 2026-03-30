# 核心页面实例规格

> **OWNER**: Skill Hub 前端负责人
>
> **Last reviewed**: 2026-03-28
>
> **Change triggers**: 关键页面区块结构 / 主操作路径 / 抽屉与弹窗行为 / 权限态与异常态

## Purpose
本文件将 `page-spec-template.md` 落到当前 Skill Hub 的核心页面，避免页面设计仍然停留在“原则正确，但没有具体实例”的状态。

## 前台技能广场
### 页面身份
- 页面类型：列表页
- 目标用户：普通探索用户、贡献者
- 路由：`/` 或技能广场首页

### 页面目标
- 用户第一眼看到可探索 skill
- 不把平台说明放在技能列表之前
- 保留从探索到详情、点赞/收藏/下载、进入上传中心的连续链路

### 区块结构
| 区块 | 作用 | 稳定 `id` |
|---|---|---|
| 顶部头区 | 标题、上传入口、次级说明 | `portal-marketplace-header` |
| 分类区 | 分类切换 | `portal-marketplace-categories` |
| 筛选区 | 搜索、排序 | `portal-marketplace-filters` |
| 技能列表 | 卡片网格 | `portal-marketplace-list` |
| 分页区 | 翻页与结果统计 | `portal-marketplace-pagination` |

### 数据来源
- 分类：`GET /api/public/categories`
- 技能列表：`GET /api/public/skills`

### 权限与状态
- 未登录也可浏览
- loading / empty / error 必须完整
- “上传我的技能”未登录时先引导登录，再进入上传中心
- 点赞 / 收藏 / 下载成功后必须给出显式反馈，不允许只靠计数变化让用户自行猜结果

## 前台技能详情抽屉
### 页面身份
- 页面类型：右侧抽屉
- 目标用户：浏览技能详情、互动与下载的用户
- 入口：点击技能卡片

### 区块结构
| 区块 | 作用 | 稳定 `id` |
|---|---|---|
| 抽屉头部 | 技能名、分类、版本、关闭按钮 | `portal-skill-detail-header` |
| 统计与操作 | 点赞、收藏、下载 | `portal-skill-detail-actions` |
| 使用方式 | Agent / Human tabs | `portal-skill-detail-usage` |
| README 与说明 | 正文与 changelog | `portal-skill-detail-content` |
| 历史版本 | 历史版本摘要 | `portal-skill-detail-versions` |

### 数据来源
- `GET /api/public/skills/{slug}`

### 状态要求
- 详情加载中必须有骨架，不允许白板
- skill 不存在或不可见时显示可读错误
- 登录失效时互动按钮给出重新登录提示

## 前台上传中心抽屉
### 页面身份
- 页面类型：右侧抽屉
- 目标用户：贡献者
- 入口：前台“上传我的技能”按钮

### 区块结构
| 区块 | 作用 | 稳定 `id` |
|---|---|---|
| 头部摘要 | 当前用户可做什么 | `portal-upload-center-header` |
| 直接上传区 | 拖拽或点击选择 ZIP 后立即上传 | `portal-upload-center-dropzone` |
| 上传记录 | 当前用户自己的投稿记录 | `portal-upload-center-list` |

### 数据来源
- `GET /api/public/upload-center/records`
- `POST /api/admin/skills/upload`

### 权限与状态
- 未登录：提示登录，不直接跳后台
- 已登录但无记录：显示空态并保留拖拽上传区
- 已登录但无 `skill.upload`：显示权限说明，不展示可操作上传区
- 前台记录只展示当前用户的上传结果、审核状态和最近处理意见，不展示后台治理字段
- 投稿成功后必须在当前抽屉给出成功反馈，并让上传记录自动刷新到最新状态

## 后台技能列表
### 页面身份
- 页面类型：工作台列表页
- 目标用户：管理员、维护者、审核者、发布者
- 路由：后台技能列表入口

### 区块结构
| 区块 | 作用 | 稳定 `id` |
|---|---|---|
| 筛选区 | 关键词、分类、状态 | `admin-skills-filters` |
| 摘要区 | 总量与待办摘要 | `admin-skills-summary` |
| 表格区 | 主档列表 | `admin-skills-table` |

### 数据来源
- `GET /api/admin/skills`

### 关键列
- 名称
- slug
- 分类
- 主档状态
- 最新版本状态
- 当前线上版本
- 待审核数
- 待发布数
- 负责人
- 最近更新时间

## 后台技能详情
### 页面身份
- 页面类型：详情页
- 目标用户：维护者、审核者、发布者、管理员

### 区块结构
| 区块 | 作用 | 稳定 `id` |
|---|---|---|
| 主档信息 | 基本字段与主操作 | `admin-skill-detail-overview` |
| 版本时间线 | 版本与审核摘要 | `admin-skill-detail-versions` |
| 授权对象 | role grant / user grant | `admin-skill-detail-grants` |
| 数据统计 | 聚合统计与趋势 | `admin-skill-detail-stats` |
| 明细记录 | 收藏/下载明细 | `admin-skill-detail-records` |

### 数据来源
- `GET /api/admin/skills/{id}`
- `GET /api/admin/skills/{id}/stats`
- `GET /api/admin/skills/{id}/favorites`
- `GET /api/admin/skills/{id}/downloads`
- `GET /api/admin/skills/{id}/permissions`

### 状态与权限
- 权限不足时显示只读原因，不允许整页空白
- 模块容器与间距固定统一，不允许某个卡片独立漂移
- 主档保存、上传新版本、授权新增/移除都必须给出明确反馈；授权移除属于高风险动作，必须二次确认

## 后台审核中心
### 页面身份
- 页面类型：工作台页
- 目标用户：reviewer / admin

### 区块结构
| 区块 | 作用 | 稳定 `id` |
|---|---|---|
| 筛选区 | 分类、提交人、关键词 | `admin-reviews-filters` |
| 摘要区 | 待审核数、最近变更 | `admin-reviews-summary` |
| 列表区 | submitted 版本队列 | `admin-reviews-table` |
| 详情弹窗 | 审核详情与动作 | `admin-reviews-detail-modal` |

### 数据来源
- `GET /api/admin/reviews/pending`

### 关键动作
- 通过
- 拒绝

### 行为要求
- 通过后移出当前队列并进入待发布
- 拒绝后要求填写意见
- 动作失败必须保留筛选与上下文
- 通过 / 拒绝提交前必须二次确认；提交成功后必须给出显式成功反馈

## 后台待发布
### 页面身份
- 页面类型：工作台页
- 目标用户：publisher / admin

### 数据来源
- `GET /api/admin/releases/pending`

### 区块结构
- `admin-releases-filters`
- `admin-releases-summary`
- `admin-releases-table`

### 核心行为
- 只处理 `approved`
- 发布成功后立即刷新列表、技能详情摘要和前台线上可见版本
- 发布前必须二次确认，确认文案中要明确“旧线上版本会自动归档”；发布成功后必须给出显式成功反馈

## 后台处理记录
### 页面身份
- 页面类型：工作台页
- 目标用户：reviewer / publisher / admin

### 数据来源
- `GET /api/admin/reviews/history`

### 核心行为
- 默认时间倒序
- 支持时间、分类、skill、提交人、审核人、发布人过滤
- 行点击可进入版本详情

## 后台版本详情
### 页面身份
- 页面类型：详情页 / 弹窗详情
- 目标用户：维护者、审核者、发布者、管理员

### 区块结构
| 区块 | 作用 | 稳定 `id` |
|---|---|---|
| 状态摘要 | 当前状态、版本号、能力按钮 | `admin-version-detail-summary` |
| manifest 区 | 结构化字段 | `admin-version-detail-manifest` |
| README 区 | 文档预览 | `admin-version-detail-readme` |
| 使用方式区 | usage guide 编辑或只读 | `admin-version-detail-usage` |
| 审核记录区 | 最近动作 | `admin-version-detail-reviews` |

### 数据来源
- `GET /api/admin/versions/{id}`

### 动作要求
- 按 capability 显示按钮
- `draft/rejected`：编辑、提审
- `submitted`：审核通过/拒绝
- `approved`：发布
- `published`：归档、回滚（按权限）

## Verification
- [ ] 关键页面均有实例规格，不再只有模板
- [ ] 页面区块、数据来源、权限态、异常态都能从规格文档中直接查到
- [ ] E2E 稳定 `id` 与页面区块定义一致
