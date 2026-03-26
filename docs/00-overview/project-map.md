# 项目地图

## 产品目标
Skill Hub 是公司内部技能广场与治理平台，目标不是“放一堆技能文件”，而是把 skill 的发现、上传、审核、发布、授权、统计和追溯串成可运营闭环。

## 角色地图
### 普通用户
- 浏览技能
- 打开详情
- 点赞、收藏、下载
- 通过 Agent/Human 指引使用 skill

### 贡献者
- 上传 skill
- 上传新版本
- 编辑草稿或被拒绝版本
- 提交审核

### 审核 / 发布 / 运营 / 管理员
- 审核待审版本
- 从待发布队列正式上线
- 配置 skill 授权
- 查看统计和明细
- 管理分类、用户、角色和审计

## 代码地图
- `apps/portal-web`：用户端技能广场
- `apps/admin-web`：管理后台
- `apps/api-server`：FastAPI 后端
- `docs`：工程规范、架构说明、业务流程、运行手册、协作提示词
- `infra`：本地脚本、systemd、nginx、发布检查脚本

## 核心能力地图
### 用户侧
- 技能广场列表
- 详情抽屉
- 点赞 / 收藏 / 下载
- 用户侧上传入口

### 后台侧
- 技能列表
- 技能详情 / 版本详情
- 审核中心
- 待发布
- 处理记录
- 分类、用户、角色、审计管理

### 平台底座
- ZIP 上传解析
- 版本状态机
- 全局权限 + skill 级授权
- 审计日志
- 统计汇总与明细

## 关键术语
- Skill：技能主档，不随版本变化的实体
- Skill Version：技能版本，可被审核和发布
- Pending Review：`submitted`，待审核
- Pending Release：`approved`，待发布
- Published：当前线上可见版本
- Archived：历史下线版本
- Skill Grant：某个 skill 上授予角色或用户的操作范围
- Global Permission：角色聚合得到的后台能力
- Skill Scope：作用在单个 skill 上的细粒度授权
